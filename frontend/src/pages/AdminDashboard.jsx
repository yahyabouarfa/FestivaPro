import { useEffect, useMemo, useState } from 'react';
import {
  BadgeDollarSign,
  Boxes,
  CalendarDays,
  ClipboardList,
  Dice5,
  Package,
  Plus,
  ReceiptText,
  Store,
  UsersRound,
} from 'lucide-react';
import { api } from '../api/client.js';
import ResourcePanel from '../components/ResourcePanel.jsx';

const blankUser = { full_name: '', email: '', phone_number: '', role: 'employee', password: '', is_active: true };
const blankEvent = { name: '', location: '', starts_at: '', ends_at: '', is_active: true };
const blankBar = { event_id: '', name: '', location: '', starting_cash: '0' };
const blankProduct = { name: '', sku: '', unit: 'unit', is_active: true };
const blankPrice = { event_id: '', product_id: '', price: '', cost_price: '0' };
const blankAssignment = { event_id: '', bar_id: '', user_id: '', shift_salary: '0' };
const blankStock = { bar_id: '', product_id: '', opening_quantity: '0', current_quantity: '0' };
const blankSale = { event_id: '', bar_id: '', product_id: '', employee_id: '', quantity: '1', unit_price: '' };

function toApiDate(value) {
  return value ? new Date(value).toISOString() : value;
}

function money(value) {
  return Number(value || 0).toLocaleString(undefined, { style: 'currency', currency: 'USD' });
}

export default function AdminDashboard() {
  const [users, setUsers] = useState([]);
  const [events, setEvents] = useState([]);
  const [bars, setBars] = useState([]);
  const [products, setProducts] = useState([]);
  const [prices, setPrices] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [stock, setStock] = useState([]);
  const [summary, setSummary] = useState(null);
  const [message, setMessage] = useState('');
  const [forms, setForms] = useState({
    user: blankUser,
    event: blankEvent,
    bar: blankBar,
    product: blankProduct,
    price: blankPrice,
    assignment: blankAssignment,
    stock: blankStock,
    sale: blankSale,
    reportEventId: '',
    randomEventId: '',
    randomSalary: '0',
  });

  const employees = useMemo(() => users.filter((user) => user.role === 'employee' && user.is_active), [users]);

  async function loadAll() {
    const [userRes, eventRes, barRes, productRes, priceRes, assignmentRes, stockRes] = await Promise.all([
      api.get('/admin/users'),
      api.get('/admin/events'),
      api.get('/admin/bars'),
      api.get('/admin/products'),
      api.get('/admin/prices'),
      api.get('/admin/assignments'),
      api.get('/admin/stock'),
    ]);
    setUsers(userRes.data);
    setEvents(eventRes.data);
    setBars(barRes.data);
    setProducts(productRes.data);
    setPrices(priceRes.data);
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

  async function createEvent(event) {
    event.preventDefault();
    await submit('event', '/admin/events', { ...forms.event, starts_at: toApiDate(forms.event.starts_at), ends_at: toApiDate(forms.event.ends_at) }, blankEvent);
  }

  async function createSale(event) {
    event.preventDefault();
    await submit('sale', '/admin/sales', forms.sale, blankSale);
  }

  async function randomAssign() {
    setMessage('');
    try {
      await api.post('/admin/assignments/random', {
        event_id: forms.randomEventId,
        shift_salary: forms.randomSalary,
      });
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
          <form className="compact-form" onSubmit={createEvent}>
            <input placeholder="Name" value={forms.event.name} onChange={(e) => setForm('event', 'name', e.target.value)} required />
            <input placeholder="Location" value={forms.event.location} onChange={(e) => setForm('event', 'location', e.target.value)} />
            <input value={forms.event.starts_at} onChange={(e) => setForm('event', 'starts_at', e.target.value)} required type="datetime-local" />
            <input value={forms.event.ends_at} onChange={(e) => setForm('event', 'ends_at', e.target.value)} required type="datetime-local" />
            <button className="primary-button" type="submit"><Plus size={16} />Add</button>
          </form>
          <DataTable columns={['Event', 'Location', 'Starts']} rows={events.map((e) => [e.name, e.location || '-', new Date(e.starts_at).toLocaleString()])} />
        </ResourcePanel>

        <ResourcePanel title="Bars" icon={<Store size={18} />}>
          <form className="compact-form" onSubmit={(event) => { event.preventDefault(); submit('bar', '/admin/bars', forms.bar, blankBar); }}>
            <Select value={forms.bar.event_id} onChange={(v) => setForm('bar', 'event_id', v)} options={events} label="Event" />
            <input placeholder="Bar name" value={forms.bar.name} onChange={(e) => setForm('bar', 'name', e.target.value)} required />
            <input placeholder="Location" value={forms.bar.location} onChange={(e) => setForm('bar', 'location', e.target.value)} />
            <input placeholder="Starting cash" value={forms.bar.starting_cash} onChange={(e) => setForm('bar', 'starting_cash', e.target.value)} type="number" />
            <button className="primary-button" type="submit"><Plus size={16} />Add</button>
          </form>
          <DataTable columns={['Bar', 'Event', 'Cash']} rows={bars.map((b) => [b.name, eventName(events, b.event_id), money(b.starting_cash)])} />
        </ResourcePanel>

        <ResourcePanel title="Products" icon={<Package size={18} />}>
          <form className="compact-form" onSubmit={(event) => { event.preventDefault(); submit('product', '/admin/products', forms.product, blankProduct); }}>
            <input placeholder="Name" value={forms.product.name} onChange={(e) => setForm('product', 'name', e.target.value)} required />
            <input placeholder="SKU" value={forms.product.sku} onChange={(e) => setForm('product', 'sku', e.target.value)} required />
            <input placeholder="Unit" value={forms.product.unit} onChange={(e) => setForm('product', 'unit', e.target.value)} />
            <button className="primary-button" type="submit"><Plus size={16} />Add</button>
          </form>
          <DataTable columns={['Product', 'SKU', 'Unit']} rows={products.map((p) => [p.name, p.sku, p.unit])} />
        </ResourcePanel>

        <ResourcePanel title="Pricing" icon={<BadgeDollarSign size={18} />}>
          <form className="compact-form" onSubmit={(event) => { event.preventDefault(); submit('price', '/admin/prices', forms.price, blankPrice); }}>
            <Select value={forms.price.event_id} onChange={(v) => setForm('price', 'event_id', v)} options={events} label="Event" />
            <Select value={forms.price.product_id} onChange={(v) => setForm('price', 'product_id', v)} options={products} label="Product" />
            <input placeholder="Sale price" value={forms.price.price} onChange={(e) => setForm('price', 'price', e.target.value)} required type="number" />
            <input placeholder="Cost" value={forms.price.cost_price} onChange={(e) => setForm('price', 'cost_price', e.target.value)} type="number" />
            <button className="primary-button" type="submit"><Plus size={16} />Set</button>
          </form>
          <DataTable columns={['Event', 'Product', 'Price']} rows={prices.map((p) => [eventName(events, p.event_id), productName(products, p.product_id), money(p.price)])} />
        </ResourcePanel>

        <ResourcePanel title="Assignments" icon={<ClipboardList size={18} />}>
          <form className="compact-form" onSubmit={(event) => { event.preventDefault(); submit('assignment', '/admin/assignments', forms.assignment, blankAssignment); }}>
            <Select value={forms.assignment.event_id} onChange={(v) => setForm('assignment', 'event_id', v)} options={events} label="Event" />
            <Select value={forms.assignment.bar_id} onChange={(v) => setForm('assignment', 'bar_id', v)} options={bars} label="Bar" />
            <Select value={forms.assignment.user_id} onChange={(v) => setForm('assignment', 'user_id', v)} options={employees} label="Employee" />
            <input placeholder="Salary" value={forms.assignment.shift_salary} onChange={(e) => setForm('assignment', 'shift_salary', e.target.value)} type="number" />
            <button className="primary-button" type="submit"><Plus size={16} />Assign</button>
          </form>
          <div className="inline-tools">
            <Select value={forms.randomEventId} onChange={(v) => setForms((c) => ({ ...c, randomEventId: v }))} options={events} label="Event" />
            <input value={forms.randomSalary} onChange={(e) => setForms((c) => ({ ...c, randomSalary: e.target.value }))} type="number" />
            <button className="secondary-button" onClick={randomAssign} type="button"><Dice5 size={16} />Random</button>
          </div>
          <DataTable columns={['Employee', 'Bar', 'Salary']} rows={assignments.map((a) => [userName(users, a.user_id), barName(bars, a.bar_id), money(a.shift_salary)])} />
        </ResourcePanel>

        <ResourcePanel title="Stock" icon={<Boxes size={18} />}>
          <form className="compact-form" onSubmit={(event) => { event.preventDefault(); submit('stock', '/admin/stock', forms.stock, blankStock); }}>
            <Select value={forms.stock.bar_id} onChange={(v) => setForm('stock', 'bar_id', v)} options={bars} label="Bar" />
            <Select value={forms.stock.product_id} onChange={(v) => setForm('stock', 'product_id', v)} options={products} label="Product" />
            <input placeholder="Opening" value={forms.stock.opening_quantity} onChange={(e) => setForm('stock', 'opening_quantity', e.target.value)} type="number" />
            <input placeholder="Current" value={forms.stock.current_quantity} onChange={(e) => setForm('stock', 'current_quantity', e.target.value)} type="number" />
            <button className="primary-button" type="submit"><Plus size={16} />Set</button>
          </form>
          <DataTable columns={['Bar', 'Product', 'Current']} rows={stock.map((s) => [barName(bars, s.bar_id), productName(products, s.product_id), s.current_quantity])} />
        </ResourcePanel>

        <ResourcePanel title="Sales & Reports" icon={<ReceiptText size={18} />}>
          <form className="compact-form" onSubmit={createSale}>
            <Select value={forms.sale.event_id} onChange={(v) => setForm('sale', 'event_id', v)} options={events} label="Event" />
            <Select value={forms.sale.bar_id} onChange={(v) => setForm('sale', 'bar_id', v)} options={bars} label="Bar" />
            <Select value={forms.sale.product_id} onChange={(v) => setForm('sale', 'product_id', v)} options={products} label="Product" />
            <Select value={forms.sale.employee_id} onChange={(v) => setForm('sale', 'employee_id', v)} options={employees} label="Employee" />
            <input placeholder="Qty" value={forms.sale.quantity} onChange={(e) => setForm('sale', 'quantity', e.target.value)} type="number" />
            <input placeholder="Unit price" value={forms.sale.unit_price} onChange={(e) => setForm('sale', 'unit_price', e.target.value)} type="number" />
            <button className="primary-button" type="submit"><Plus size={16} />Record</button>
          </form>
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

function productName(products, id) {
  return products.find((product) => Number(product.id) === Number(id))?.name || `Product ${id}`;
}

function barName(bars, id) {
  return bars.find((bar) => Number(bar.id) === Number(id))?.name || `Bar ${id}`;
}

function userName(users, id) {
  return users.find((user) => Number(user.id) === Number(id))?.full_name || `User ${id}`;
}
