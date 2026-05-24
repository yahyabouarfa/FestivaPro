import { useEffect, useMemo, useState } from 'react';
import {
  BadgeDollarSign,
  Boxes,
  CalendarDays,
  ClipboardList,
  Dice5,
  FolderTree,
  Package,
  Plus,
  ReceiptText,
  Store,
  UsersRound,
} from 'lucide-react';
import { api } from '../api/client.js';
import ResourcePanel from '../components/ResourcePanel.jsx';

const blankUser = { full_name: '', email: '', phone_number: '', role: 'employee', password: '', is_active: true };
const blankEvent = { name: '', location: '', event_date: '', start_time: '', end_time: '', status: 'upcoming' };
const blankBar = { event_id: '', name: '', responsible_user_id: '' };
const blankCategory = { name: '' };
const blankProduct = { name: '', category_id: '', unit: 'unit' };
const blankEventStock = { event_id: '', product_id: '', quantity_total: '0', bought_price_per_unit: '0', selling_price_per_unit: '0' };
const blankAssignment = { bar_id: '', user_id: '' };
const blankStock = { bar_id: '', product_id: '', quantity_allocated: '0', quantity_remaining: '0' };

function money(value) {
  return Number(value || 0).toLocaleString(undefined, { style: 'currency', currency: 'MAD' });
}

export default function AdminDashboard() {
  const [users, setUsers] = useState([]);
  const [events, setEvents] = useState([]);
  const [bars, setBars] = useState([]);
  const [categories, setCategories] = useState([]);
  const [products, setProducts] = useState([]);
  const [eventStock, setEventStock] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [stock, setStock] = useState([]);
  const [summary, setSummary] = useState(null);
  const [message, setMessage] = useState('');
  const [forms, setForms] = useState({
    user: blankUser,
    event: blankEvent,
    bar: blankBar,
    category: blankCategory,
    product: blankProduct,
    eventStock: blankEventStock,
    assignment: blankAssignment,
    stock: blankStock,
    reportEventId: '',
    randomEventId: '',
  });

  const employees = useMemo(() => users.filter((user) => user.role === 'employee' && user.is_active), [users]);

  async function loadAll() {
    const [userRes, eventRes, barRes, categoryRes, productRes, eventStockRes, assignmentRes, stockRes] = await Promise.all([
      api.get('/admin/users'),
      api.get('/admin/events'),
      api.get('/admin/bars'),
      api.get('/admin/product-categories'),
      api.get('/admin/products'),
      api.get('/admin/event-stock'),
      api.get('/admin/assignments'),
      api.get('/admin/stock'),
    ]);
    setUsers(userRes.data);
    setEvents(eventRes.data);
    setBars(barRes.data);
    setCategories(categoryRes.data);
    setProducts(productRes.data);
    setEventStock(eventStockRes.data);
    setAssignments(assignmentRes.data);
    setStock(stockRes.data);
  }

  useEffect(() => {
    loadAll().catch((err) => setMessage(err.response?.data?.detail || 'Unable to load admin data.'));
  }, []);

  function setForm(name, field, value) {
    setForms((current) => ({ ...current, [name]: { ...current[name], [field]: value } }));
  }

  async function submit(name, endpoint, payload, resetValue) {
    setMessage('');
    try {
      await api.post(endpoint, payload);
      setForms((current) => ({ ...current, [name]: resetValue }));
      await loadAll();
      setMessage('Saved successfully.');
    } catch (err) {
      setMessage(err.response?.data?.detail || 'Save failed.');
    }
  }

  async function randomAssign() {
    if (!forms.randomEventId) return;
    setMessage('');
    try {
      await api.post('/admin/assignments/random', { event_id: forms.randomEventId });
      await loadAll();
      setMessage('Random assignment completed.');
    } catch (err) {
      setMessage(err.response?.data?.detail || 'Random assignment failed.');
    }
  }

  async function loadSummary() {
    if (!forms.reportEventId) return;
    const { data } = await api.get('/admin/reports/summary', { params: { event_id: forms.reportEventId } });
    setSummary(data);
  }

  return (
    <main className="workspace">
      <div className="page-title">
        <div>
          <h1>Admin command center</h1>
          <p>Events, bars, stock, prices, staffing, and night-end reporting.</p>
        </div>
        {message && <div className="status-pill">{message}</div>}
      </div>

      <section className="metric-strip">
        <div><span>{events.length}</span> Events</div>
        <div><span>{bars.length}</span> Bars</div>
        <div><span>{products.length}</span> Products</div>
        <div><span>{employees.length}</span> Bartenders</div>
      </section>

      <div className="resource-grid">
        <ResourcePanel title="Users" icon={<UsersRound size={18} />}>
          <form className="compact-form" onSubmit={(event) => { event.preventDefault(); submit('user', '/admin/users', forms.user, blankUser); }}>
            <input placeholder="Full name" value={forms.user.full_name} onChange={(e) => setForm('user', 'full_name', e.target.value)} required />
            <input placeholder="Email" value={forms.user.email} onChange={(e) => setForm('user', 'email', e.target.value)} required type="email" />
            <input placeholder="Phone" value={forms.user.phone_number} onChange={(e) => setForm('user', 'phone_number', e.target.value)} />
            <select value={forms.user.role} onChange={(e) => setForm('user', 'role', e.target.value)}>
              <option value="employee">Employee</option>
              <option value="admin">Admin</option>
            </select>
            <input placeholder="Password" value={forms.user.password} onChange={(e) => setForm('user', 'password', e.target.value)} required type="password" />
            <button className="primary-button" type="submit"><Plus size={16} />Add</button>
          </form>
          <DataTable columns={['Name', 'Role', 'Email']} rows={users.map((u) => [u.full_name, u.role, u.email])} />
        </ResourcePanel>

        <ResourcePanel title="Events" icon={<CalendarDays size={18} />}>
          <form className="compact-form" onSubmit={(event) => { event.preventDefault(); submit('event', '/admin/events', forms.event, blankEvent); }}>
            <input placeholder="Name" value={forms.event.name} onChange={(e) => setForm('event', 'name', e.target.value)} required />
            <input placeholder="Moroccan city" value={forms.event.location} onChange={(e) => setForm('event', 'location', e.target.value)} required />
            <input value={forms.event.event_date} onChange={(e) => setForm('event', 'event_date', e.target.value)} required type="date" />
            <input value={forms.event.start_time} onChange={(e) => setForm('event', 'start_time', e.target.value)} required type="time" />
            <input value={forms.event.end_time} onChange={(e) => setForm('event', 'end_time', e.target.value)} required type="time" />
            <select value={forms.event.status} onChange={(e) => setForm('event', 'status', e.target.value)}>
              <option value="upcoming">Upcoming</option>
              <option value="active">Active</option>
              <option value="closed">Closed</option>
            </select>
            <button className="primary-button" type="submit"><Plus size={16} />Add</button>
          </form>
          <DataTable columns={['Event', 'City', 'Date', 'Status']} rows={events.map((e) => [e.name, e.location, e.event_date, e.status])} />
        </ResourcePanel>

        <ResourcePanel title="Bars" icon={<Store size={18} />}>
          <form className="compact-form" onSubmit={(event) => { event.preventDefault(); submit('bar', '/admin/bars', forms.bar, blankBar); }}>
            <Select value={forms.bar.event_id} onChange={(v) => setForm('bar', 'event_id', v)} options={events} label="Event" />
            <input placeholder="Bar name" value={forms.bar.name} onChange={(e) => setForm('bar', 'name', e.target.value)} required />
            <Select value={forms.bar.responsible_user_id} onChange={(v) => setForm('bar', 'responsible_user_id', v)} options={employees} label="Responsible" />
            <button className="primary-button" type="submit"><Plus size={16} />Add</button>
          </form>
          <DataTable columns={['Bar', 'Event', 'Responsible']} rows={bars.map((b) => [b.name, eventName(events, b.event_id), userName(users, b.responsible_user_id)])} />
        </ResourcePanel>

        <ResourcePanel title="Categories" icon={<FolderTree size={18} />}>
          <form className="compact-form" onSubmit={(event) => { event.preventDefault(); submit('category', '/admin/product-categories', forms.category, blankCategory); }}>
            <input placeholder="Category name" value={forms.category.name} onChange={(e) => setForm('category', 'name', e.target.value)} required />
            <button className="primary-button" type="submit"><Plus size={16} />Add</button>
          </form>
          <DataTable columns={['Category']} rows={categories.map((c) => [c.name])} />
        </ResourcePanel>

        <ResourcePanel title="Products" icon={<Package size={18} />}>
          <form className="compact-form" onSubmit={(event) => { event.preventDefault(); submit('product', '/admin/products', forms.product, blankProduct); }}>
            <input placeholder="Name" value={forms.product.name} onChange={(e) => setForm('product', 'name', e.target.value)} required />
            <Select value={forms.product.category_id} onChange={(v) => setForm('product', 'category_id', v)} options={categories} label="Category" />
            <select value={forms.product.unit} onChange={(e) => setForm('product', 'unit', e.target.value)}>
              <option value="bottle">Bottle</option>
              <option value="can">Can</option>
              <option value="unit">Unit</option>
            </select>
            <button className="primary-button" type="submit"><Plus size={16} />Add</button>
          </form>
          <DataTable columns={['Product', 'Category', 'Unit']} rows={products.map((p) => [p.name, categoryName(categories, p.category_id), p.unit])} />
        </ResourcePanel>

        <ResourcePanel title="Event Stock" icon={<BadgeDollarSign size={18} />}>
          <form className="compact-form" onSubmit={(event) => { event.preventDefault(); submit('eventStock', '/admin/event-stock', forms.eventStock, blankEventStock); }}>
            <Select value={forms.eventStock.event_id} onChange={(v) => setForm('eventStock', 'event_id', v)} options={events} label="Event" />
            <Select value={forms.eventStock.product_id} onChange={(v) => setForm('eventStock', 'product_id', v)} options={products} label="Product" />
            <input placeholder="Total qty" value={forms.eventStock.quantity_total} onChange={(e) => setForm('eventStock', 'quantity_total', e.target.value)} required type="number" />
            <input placeholder="Bought price" value={forms.eventStock.bought_price_per_unit} onChange={(e) => setForm('eventStock', 'bought_price_per_unit', e.target.value)} required type="number" />
            <input placeholder="Selling price" value={forms.eventStock.selling_price_per_unit} onChange={(e) => setForm('eventStock', 'selling_price_per_unit', e.target.value)} required type="number" />
            <button className="primary-button" type="submit"><Plus size={16} />Set</button>
          </form>
          <DataTable columns={['Event', 'Product', 'Total', 'Sell']} rows={eventStock.map((s) => [eventName(events, s.event_id), productName(products, s.product_id), s.quantity_total, money(s.selling_price_per_unit)])} />
        </ResourcePanel>

        <ResourcePanel title="Assignments" icon={<ClipboardList size={18} />}>
          <form className="compact-form" onSubmit={(event) => { event.preventDefault(); submit('assignment', '/admin/assignments', forms.assignment, blankAssignment); }}>
            <Select value={forms.assignment.bar_id} onChange={(v) => setForm('assignment', 'bar_id', v)} options={bars} label="Bar" />
            <Select value={forms.assignment.user_id} onChange={(v) => setForm('assignment', 'user_id', v)} options={employees} label="Employee" />
            <button className="primary-button" type="submit"><Plus size={16} />Assign</button>
          </form>
          <div className="inline-tools">
            <Select value={forms.randomEventId} onChange={(v) => setForms((c) => ({ ...c, randomEventId: v }))} options={events} label="Event" />
            <button className="secondary-button" onClick={randomAssign} type="button"><Dice5 size={16} />Random</button>
          </div>
          <DataTable columns={['Employee', 'Bar']} rows={assignments.map((a) => [userName(users, a.user_id), barName(bars, a.bar_id)])} />
        </ResourcePanel>

        <ResourcePanel title="Bar Stock" icon={<Boxes size={18} />}>
          <form className="compact-form" onSubmit={(event) => { event.preventDefault(); submit('stock', '/admin/stock', forms.stock, blankStock); }}>
            <Select value={forms.stock.bar_id} onChange={(v) => setForm('stock', 'bar_id', v)} options={bars} label="Bar" />
            <Select value={forms.stock.product_id} onChange={(v) => setForm('stock', 'product_id', v)} options={products} label="Product" />
            <input placeholder="Allocated" value={forms.stock.quantity_allocated} onChange={(e) => setForm('stock', 'quantity_allocated', e.target.value)} type="number" />
            <input placeholder="Remaining" value={forms.stock.quantity_remaining} onChange={(e) => setForm('stock', 'quantity_remaining', e.target.value)} type="number" />
            <button className="primary-button" type="submit"><Plus size={16} />Set</button>
          </form>
          <DataTable columns={['Bar', 'Product', 'Allocated', 'Remaining', 'Sold']} rows={stock.map((s) => [barName(bars, s.bar_id), productName(products, s.product_id), s.quantity_allocated, s.quantity_remaining, s.quantity_sold])} />
        </ResourcePanel>

        <ResourcePanel title="Reports" icon={<ReceiptText size={18} />}>
          <div className="inline-tools">
            <Select value={forms.reportEventId} onChange={(v) => setForms((c) => ({ ...c, reportEventId: v }))} options={events} label="Event" />
            <button className="secondary-button" onClick={loadSummary} type="button">Summary</button>
          </div>
          {summary && (
            <div className="summary-grid">
              <span>Revenue <strong>{money(summary.revenue)}</strong></span>
              <span>Cost <strong>{money(summary.cost)}</strong></span>
              <span>Salaries <strong>{money(summary.salaries)}</strong></span>
              <span>Profit <strong>{money(summary.profit)}</strong></span>
            </div>
          )}
        </ResourcePanel>
      </div>
    </main>
  );
}

function Select({ value, onChange, options, label }) {
  return (
    <select value={value} onChange={(event) => onChange(event.target.value)} required>
      <option value="">{label}</option>
      {options.map((option) => (
        <option key={option.id} value={option.id}>
          {option.name || option.full_name}
        </option>
      ))}
    </select>
  );
}

function DataTable({ columns, rows }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr><td colSpan={columns.length}>No records yet.</td></tr>
          ) : (
            rows.map((row, index) => (
              <tr key={index}>{row.map((cell, cellIndex) => <td key={cellIndex}>{cell}</td>)}</tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

function eventName(events, id) {
  return events.find((event) => Number(event.id) === Number(id))?.name || `Event ${id}`;
}

function categoryName(categories, id) {
  return categories.find((category) => Number(category.id) === Number(id))?.name || `Category ${id}`;
}

function productName(products, id) {
  return products.find((product) => Number(product.id) === Number(id))?.name || `Product ${id}`;
}

function barName(bars, id) {
  return bars.find((bar) => Number(bar.id) === Number(id))?.name || `Bar ${id}`;
}

function userName(users, id) {
  return users.find((user) => Number(user.id) === Number(id))?.full_name || `User ${id}`;
}
