import { useEffect, useMemo, useState } from 'react';
import {
  BadgeDollarSign,
  Boxes,
  CalendarDays,
  ClipboardList,
  Download,
  Dice5,
  FolderTree,
  Package,
  Plus,
  ReceiptText,
  Store,
  UsersRound,
} from 'lucide-react';
import { Bar, BarChart, CartesianGrid, Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { api } from '../api/client.js';
import ResourcePanel from '../components/ResourcePanel.jsx';

const blankUser = { full_name: '', email: '', phone_number: '', role: 'employee', password: '', is_active: true };
const blankEvent = { name: '', location: '', event_date: '', start_time: '', end_time: '', status: 'upcoming', attendance_count: '0' };
const blankBar = { event_id: '', name: '', responsible_user_id: '' };
const blankCategory = { name: '' };
const blankProduct = { name: '', category_id: '', unit: 'unit' };
const blankEventStock = { event_id: '', product_id: '', quantity_total: '0', bought_price_per_unit: '0', selling_price_per_unit: '0' };
const blankAssignment = { event_id: '', bar_id: '', user_id: '', salary_amount: '0' };
const blankStock = { bar_id: '', product_id: '', quantity_allocated: '0', quantity_remaining: '0' };
const blankNight = { event_id: '', bar_id: '', product_id: '', quantity_remaining: '0', user_id: '', units_sold: '0', sales_amount: '', contribution_pct: '' };

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
  const [bartenderSales, setBartenderSales] = useState([]);
  const [priceHistory, setPriceHistory] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [lowStock, setLowStock] = useState([]);
  const [summary, setSummary] = useState(null);
  const [insights, setInsights] = useState(null);
  const [comparison, setComparison] = useState([]);
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
    night: blankNight,
    reportEventId: '',
    reportBarId: '',
    randomEventId: '',
    randomSalary: '0',
  });

  const employees = useMemo(() => users.filter((user) => user.role === 'employee' && user.is_active), [users]);
  const eventBars = useMemo(() => bars.filter((bar) => Number(bar.event_id) === Number(forms.reportEventId)), [bars, forms.reportEventId]);
  const chartBars = useMemo(() => (insights?.best_sellers || []).slice(0, 8).map((item) => ({ name: item.product_name, sold: Number(item.quantity_sold || 0), revenue: Number(item.revenue || 0) })), [insights]);
  const profitChart = useMemo(() => comparison.map((event) => ({ name: event.event_name, profit: Number(event.profit || 0), revenue: Number(event.revenue || 0) })).reverse(), [comparison]);

  async function loadAll() {
    const [userRes, eventRes, barRes, categoryRes, productRes, eventStockRes, assignmentRes, stockRes, bartenderSaleRes, priceHistoryRes, auditRes] = await Promise.all([
      api.get('/admin/users'),
      api.get('/admin/events'),
      api.get('/admin/bars'),
      api.get('/admin/product-categories'),
      api.get('/admin/products'),
      api.get('/admin/event-stock'),
      api.get('/admin/assignments'),
      api.get('/admin/stock'),
      api.get('/admin/bartender-sales'),
      api.get('/admin/price-history'),
      api.get('/admin/audit-logs'),
    ]);
    setUsers(userRes.data);
    setEvents(eventRes.data);
    setBars(barRes.data);
    setCategories(categoryRes.data);
    setProducts(productRes.data);
    setEventStock(eventStockRes.data);
    setAssignments(assignmentRes.data);
    setStock(stockRes.data);
    setBartenderSales(bartenderSaleRes.data);
    setPriceHistory(priceHistoryRes.data);
    setAuditLogs(auditRes.data);
  }

  useEffect(() => {
    loadAll().catch((err) => setMessage(err.response?.data?.detail || 'Unable to load admin data.'));
  }, []);

  useEffect(() => {
    if (!forms.reportEventId) return undefined;
    const timer = window.setInterval(async () => {
      const { data } = await api.get('/admin/reports/low-stock', { params: { event_id: forms.reportEventId } });
      setLowStock(data);
      if (data.length) setMessage(`${data.length} low-stock alert${data.length === 1 ? '' : 's'} need attention.`);
    }, 30000);
    return () => window.clearInterval(timer);
  }, [forms.reportEventId]);

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
      await api.post('/admin/assignments/random', { event_id: forms.randomEventId, salary_amount: forms.randomSalary });
      await loadAll();
      setMessage('Random assignment completed.');
    } catch (err) {
      setMessage(err.response?.data?.detail || 'Random assignment failed.');
    }
  }

  async function loadSummary() {
    if (!forms.reportEventId) return;
    const [summaryRes, insightsRes, comparisonRes, lowStockRes] = await Promise.all([
      api.get('/admin/reports/summary', { params: { event_id: forms.reportEventId } }),
      api.get('/admin/reports/event-insights', { params: { event_id: forms.reportEventId } }),
      api.get('/admin/reports/event-comparison'),
      api.get('/admin/reports/low-stock', { params: { event_id: forms.reportEventId } }),
    ]);
    setSummary(summaryRes.data);
    setInsights(insightsRes.data);
    setComparison(comparisonRes.data);
    setLowStock(lowStockRes.data);
    if (lowStockRes.data.length) setMessage(`${lowStockRes.data.length} low-stock alert${lowStockRes.data.length === 1 ? '' : 's'} need attention.`);
  }

  async function downloadReport(path) {
    const response = await api.get(path, { responseType: 'blob' });
    const disposition = response.headers['content-disposition'] || '';
    const filename = disposition.match(/filename="(.+)"/)?.[1] || 'festivapro-report';
    const url = URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
    setMessage('Report download started.');
  }

  async function recordNight(event) {
    event.preventDefault();
    const bartender_sales = forms.night.user_id
      ? [{
          user_id: forms.night.user_id,
          units_sold: forms.night.units_sold || '0',
          sales_amount: forms.night.sales_amount || null,
          contribution_pct: forms.night.contribution_pct || null,
        }]
      : [];
    await submit(
      'night',
      '/admin/end-of-night',
      {
        event_id: forms.night.event_id,
        bar_id: forms.night.bar_id,
        stock_items: [{ product_id: forms.night.product_id, quantity_remaining: forms.night.quantity_remaining }],
        bartender_sales,
      },
      blankNight,
    );
  }

  return (
    <main className="workspace">
      <div className="page-title">
        <div>
          <h1>Admin command center</h1>
          <p>Events, bars, stock, prices, staffing, and night-end reporting.</p>
        </div>
        {message && <div className={`status-pill ${message.includes('low-stock') ? 'warning' : ''}`}>{message}</div>}
      </div>

      <section className="metric-strip">
        <div className="stat-card"><span>{events.length}</span> Events</div>
        <div className="stat-card"><span>{bars.length}</span> Bars</div>
        <div className="stat-card"><span>{products.length}</span> Products</div>
        <div className="stat-card"><span>{employees.length}</span> Bartenders</div>
      </section>

      <div className="resource-grid">
        <section id="staff"><ResourcePanel title="Users" icon={<UsersRound size={18} />}>
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
        </ResourcePanel></section>

        <section id="events"><ResourcePanel title="Events" icon={<CalendarDays size={18} />}>
          <form className="compact-form" onSubmit={(event) => { event.preventDefault(); submit('event', '/admin/events', forms.event, blankEvent); }}>
            <input placeholder="Name" value={forms.event.name} onChange={(e) => setForm('event', 'name', e.target.value)} required />
            <input placeholder="Moroccan city" value={forms.event.location} onChange={(e) => setForm('event', 'location', e.target.value)} required />
            <input value={forms.event.event_date} onChange={(e) => setForm('event', 'event_date', e.target.value)} required type="date" />
            <input value={forms.event.start_time} onChange={(e) => setForm('event', 'start_time', e.target.value)} required type="time" />
            <input value={forms.event.end_time} onChange={(e) => setForm('event', 'end_time', e.target.value)} required type="time" />
            <input placeholder="Attendance" value={forms.event.attendance_count} onChange={(e) => setForm('event', 'attendance_count', e.target.value)} type="number" />
            <select value={forms.event.status} onChange={(e) => setForm('event', 'status', e.target.value)}>
              <option value="upcoming">Upcoming</option>
              <option value="active">Active</option>
              <option value="closed">Closed</option>
            </select>
            <button className="primary-button" type="submit"><Plus size={16} />Add</button>
          </form>
          <DataTable columns={['Event', 'City', 'Date', 'Attendance', 'Status']} rows={events.map((e) => [e.name, e.location, e.event_date, e.attendance_count, e.status])} />
        </ResourcePanel></section>

        <section id="bars"><ResourcePanel title="Bars" icon={<Store size={18} />}>
          <form className="compact-form" onSubmit={(event) => { event.preventDefault(); submit('bar', '/admin/bars', forms.bar, blankBar); }}>
            <Select value={forms.bar.event_id} onChange={(v) => setForm('bar', 'event_id', v)} options={events} label="Event" />
            <input placeholder="Bar name" value={forms.bar.name} onChange={(e) => setForm('bar', 'name', e.target.value)} required />
            <Select value={forms.bar.responsible_user_id} onChange={(v) => setForm('bar', 'responsible_user_id', v)} options={employees} label="Responsible" />
            <button className="primary-button" type="submit"><Plus size={16} />Add</button>
          </form>
          <DataTable columns={['Bar', 'Event', 'Responsible']} rows={bars.map((b) => [b.name, eventName(events, b.event_id), userName(users, b.responsible_user_id)])} />
        </ResourcePanel></section>

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
            <Select value={forms.assignment.event_id} onChange={(v) => setForm('assignment', 'event_id', v)} options={events} label="Event" />
            <Select value={forms.assignment.bar_id} onChange={(v) => setForm('assignment', 'bar_id', v)} options={bars} label="Bar" />
            <Select value={forms.assignment.user_id} onChange={(v) => setForm('assignment', 'user_id', v)} options={employees} label="Employee" />
            <input placeholder="Salary" value={forms.assignment.salary_amount} onChange={(e) => setForm('assignment', 'salary_amount', e.target.value)} type="number" />
            <button className="primary-button" type="submit"><Plus size={16} />Assign</button>
          </form>
          <div className="inline-tools">
            <Select value={forms.randomEventId} onChange={(v) => setForms((c) => ({ ...c, randomEventId: v }))} options={events} label="Event" />
            <input placeholder="Salary" value={forms.randomSalary} onChange={(e) => setForms((c) => ({ ...c, randomSalary: e.target.value }))} type="number" />
            <button className="secondary-button" onClick={randomAssign} type="button"><Dice5 size={16} />Random</button>
          </div>
          <DataTable columns={['Employee', 'Event', 'Bar', 'Salary']} rows={assignments.map((a) => [userName(users, a.user_id), eventName(events, a.event_id), barName(bars, a.bar_id), money(a.salary_amount)])} />
        </ResourcePanel>

        <section id="stock"><ResourcePanel title="Bar Stock" icon={<Boxes size={18} />}>
          <form className="compact-form" onSubmit={(event) => { event.preventDefault(); submit('stock', '/admin/stock', forms.stock, blankStock); }}>
            <Select value={forms.stock.bar_id} onChange={(v) => setForm('stock', 'bar_id', v)} options={bars} label="Bar" />
            <Select value={forms.stock.product_id} onChange={(v) => setForm('stock', 'product_id', v)} options={products} label="Product" />
            <input placeholder="Allocated" value={forms.stock.quantity_allocated} onChange={(e) => setForm('stock', 'quantity_allocated', e.target.value)} type="number" />
            <input placeholder="Remaining" value={forms.stock.quantity_remaining} onChange={(e) => setForm('stock', 'quantity_remaining', e.target.value)} type="number" />
            <button className="primary-button" type="submit"><Plus size={16} />Set</button>
          </form>
          <DataTable columns={['Bar', 'Product', 'Allocated', 'Remaining', 'Sold']} rows={stock.map((s) => [barName(bars, s.bar_id), productName(products, s.product_id), s.quantity_allocated, s.quantity_remaining, s.quantity_sold])} />
        </ResourcePanel></section>

        <section id="reports"><ResourcePanel title="Reports" icon={<ReceiptText size={18} />}>
          <div className="inline-tools">
            <Select value={forms.reportEventId} onChange={(v) => setForms((c) => ({ ...c, reportEventId: v }))} options={events} label="Event" />
            <button className="secondary-button" onClick={loadSummary} type="button">Summary</button>
          </div>
          <div className="inline-tools report-actions">
            <Select value={forms.reportBarId} onChange={(v) => setForms((c) => ({ ...c, reportBarId: v }))} options={eventBars.length ? eventBars : bars} label="Bar" />
            <button className="secondary-button" disabled={!forms.reportBarId} onClick={() => downloadReport(`/admin/reports/bar/${forms.reportBarId}/pdf`)} type="button"><Download size={16} />Bar PDF</button>
            <button className="secondary-button" disabled={!forms.reportBarId} onClick={() => downloadReport(`/admin/reports/bar/${forms.reportBarId}/xlsx`)} type="button"><Download size={16} />Bar XLSX</button>
            <button className="secondary-button" disabled={!forms.reportEventId} onClick={() => downloadReport(`/admin/reports/event/${forms.reportEventId}/bars/pdf`)} type="button"><Download size={16} />All Bars PDF</button>
            <button className="secondary-button" disabled={!forms.reportEventId} onClick={() => downloadReport(`/admin/reports/event/${forms.reportEventId}/full/xlsx`)} type="button"><Download size={16} />Full XLSX</button>
            <button className="primary-button" disabled={!forms.reportEventId} onClick={() => downloadReport(`/admin/reports/event/${forms.reportEventId}/bundle`)} type="button"><Download size={16} />Bundle ZIP</button>
          </div>
          {summary && (
            <div className="summary-grid">
              <span className="positive">Revenue <strong>{money(summary.revenue)}</strong></span>
              <span>Cost <strong>{money(summary.cost)}</strong></span>
              <span>Salaries <strong>{money(summary.salaries)}</strong></span>
              <span className={Number(summary.profit) >= 0 ? 'positive' : 'negative'}>Profit <strong>{money(summary.profit)}</strong></span>
            </div>
          )}
          {insights && (
            <div className="summary-grid">
              <span>Top bar <strong>{insights.top_performing_bar?.bar_name || '-'}</strong></span>
              <span>Top product <strong>{insights.top_selling_product?.product_name || '-'}</strong></span>
              <span>Top bartender <strong>{insights.highest_earning_bartender?.full_name || '-'}</strong></span>
              <span>Low stock <strong>{insights.low_stock_alerts.length}</strong></span>
              <span>Waste items <strong>{insights.waste.length}</strong></span>
            </div>
          )}
          <div className="chart-grid">
            <div className="chart-panel">
              <h3>Profit trend</h3>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={profitChart}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#33284d" />
                  <XAxis dataKey="name" stroke="#b8aee0" />
                  <YAxis stroke="#b8aee0" />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="profit" fill="#39ffb6" />
                  <Bar dataKey="revenue" fill="#ff8b2d" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="chart-panel">
              <h3>Product sales mix</h3>
              <ResponsiveContainer width="100%" height={240}>
                <PieChart>
                  <Pie data={chartBars} dataKey="sold" nameKey="name" innerRadius={44} outerRadius={86}>
                    {chartBars.map((entry, index) => <Cell key={entry.name} fill={['#39d9ff', '#ff4fd8', '#ff8b2d', '#39ffb6', '#ffd166'][index % 5]} />)}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
          {lowStock.length > 0 && <DataTable columns={['Low stock bar', 'Product', 'Remaining %']} rows={lowStock.slice(0, 8).map((item) => [item.bar_name, item.product_name, Number(item.remaining_pct).toFixed(1)])} />}
          <DataTable columns={['Event', 'Revenue', 'Profit', 'Attendance']} rows={comparison.map((e) => [e.event_name, money(e.revenue), money(e.profit), e.attendance_count])} />
        </ResourcePanel></section>

        <ResourcePanel title="End-of-Night Sales" icon={<ReceiptText size={18} />}>
          <form className="compact-form" onSubmit={recordNight}>
            <Select value={forms.night.event_id} onChange={(v) => setForm('night', 'event_id', v)} options={events} label="Event" />
            <Select value={forms.night.bar_id} onChange={(v) => setForm('night', 'bar_id', v)} options={bars} label="Bar" />
            <Select value={forms.night.product_id} onChange={(v) => setForm('night', 'product_id', v)} options={products} label="Product" />
            <input placeholder="Remaining" value={forms.night.quantity_remaining} onChange={(e) => setForm('night', 'quantity_remaining', e.target.value)} type="number" />
            <Select value={forms.night.user_id} onChange={(v) => setForm('night', 'user_id', v)} options={employees} label="Bartender" />
            <input placeholder="Units sold" value={forms.night.units_sold} onChange={(e) => setForm('night', 'units_sold', e.target.value)} type="number" />
            <input placeholder="Sales amount" value={forms.night.sales_amount} onChange={(e) => setForm('night', 'sales_amount', e.target.value)} type="number" />
            <input placeholder="Contribution %" value={forms.night.contribution_pct} onChange={(e) => setForm('night', 'contribution_pct', e.target.value)} type="number" />
            <button className="primary-button" type="submit"><Plus size={16} />Record</button>
          </form>
          <DataTable columns={['Bartender', 'Bar', 'Units', 'Sales', '%']} rows={bartenderSales.map((s) => [userName(users, s.user_id), barName(bars, s.bar_id), s.units_sold, money(s.sales_amount), s.contribution_pct])} />
        </ResourcePanel>

        <ResourcePanel title="Price History" icon={<BadgeDollarSign size={18} />}>
          <DataTable columns={['Event', 'Product', 'Old', 'New']} rows={priceHistory.slice(0, 12).map((p) => [eventName(events, p.event_id), productName(products, p.product_id), p.old_selling_price ? money(p.old_selling_price) : '-', money(p.new_selling_price)])} />
        </ResourcePanel>

        <section id="settings"><ResourcePanel title="Audit Log" icon={<ReceiptText size={18} />}>
          <DataTable columns={['When', 'Action', 'Entity', 'User']} rows={auditLogs.slice(0, 20).map((log) => [new Date(log.created_at).toLocaleString(), log.action, `${log.entity_type} #${log.entity_id || '-'}`, userName(users, log.user_id)])} />
        </ResourcePanel></section>
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
