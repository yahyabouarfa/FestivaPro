import { useEffect, useMemo, useState } from 'react';
import { Navigate, useParams } from 'react-router-dom';
import { BadgeDollarSign, CalendarDays, ClipboardList, Download, FolderTree, Moon, Package, Plus, ReceiptText, Shuffle, Store, UsersRound } from 'lucide-react';
import { api } from '../api/client.js';
import { formatApiError } from '../api/errors.js';
import ResourcePanel from '../components/ResourcePanel.jsx';

const blankUser = { full_name: '', email: '', phone_number: '', role: 'employee', password: '', is_active: true };
const blankEvent = { name: '', location: '', start_date: '', total_nights_planned: '1', attendance_count: '0' };
const blankBar = { name: '' };
const blankBeginNight = { date: '' };
const blankCategory = { name: '' };
const blankProduct = { name: '', category_id: '', unit: 'unit' };
const blankEventStock = { event_id: '', product_id: '', total_qty_purchased: '0', bought_price: '0', selling_price: '0' };
const blankNightStaff = { bar_id: '', responsible_user_id: '', salary_amount: '0' };
const blankRandomStaff = { bar_id: '', employee_count: '1', salary_amount: '0' };
const blankOpeningStock = { bar_id: '', product_id: '', qty_opening: '0', selling_price: '0' };
const blankClosingStock = { bar_id: '', product_id: '', qty_closing: '0' };
const blankClosingCash = { bar_id: '', user_id: '', cash_collected: '0' };
const blankCloseBar = { bar_id: '' };

const pageTitles = {
  events: ['Tableau des événements', 'Ouvrez un événement, puis descendez dans ses nuits et ses bars.'],
  users: ['Utilisateurs', 'Créez les administrateurs et les employés.'],
  categories: ['Catégories', 'Gérez les catégories de produits.'],
  products: ['Produits', 'Gérez les produits et leurs unités.'],
  'event-stock': ['Stock événement', 'Gérez le stock global et les prix par événement.'],
  reports: ['Rapports', 'PDF stockés, synthèses et snapshots.'],
  audit: ['Journal d’audit', 'Consultez les actions administratives.'],
};

function money(value) {
  return Number(value || 0).toLocaleString(undefined, { style: 'currency', currency: 'MAD' });
}

export default function AdminDashboard() {
  const { page } = useParams();
  const activePage = page || 'events';
  const pageMeta = pageTitles[activePage];
  const [users, setUsers] = useState([]);
  const [events, setEvents] = useState([]);
  const [eventNights, setEventNights] = useState([]);
  const [bars, setBars] = useState([]);
  const [categories, setCategories] = useState([]);
  const [products, setProducts] = useState([]);
  const [eventStock, setEventStock] = useState([]);
  const [stock, setStock] = useState([]);
  const [nightAssignments, setNightAssignments] = useState([]);
  const [bartenderCash, setBartenderCash] = useState([]);
  const [barSummaries, setBarSummaries] = useState([]);
  const [snapshots, setSnapshots] = useState([]);
  const [pdfReports, setPdfReports] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [selectedEventId, setSelectedEventId] = useState('');
  const [selectedNightId, setSelectedNightId] = useState('');
  const [message, setMessage] = useState('');
  const [forms, setForms] = useState({
    user: blankUser,
    event: blankEvent,
    bar: blankBar,
    beginNight: blankBeginNight,
    category: blankCategory,
    product: blankProduct,
    eventStock: blankEventStock,
    nightStaff: blankNightStaff,
    randomStaff: blankRandomStaff,
    openingStock: blankOpeningStock,
    closingStock: blankClosingStock,
    closingCash: blankClosingCash,
    closeBar: blankCloseBar,
  });

  const employees = useMemo(() => users.filter((user) => user.role === 'employee' && user.is_active), [users]);
  const selectedEvent = useMemo(() => events.find((event) => Number(event.id) === Number(selectedEventId)), [events, selectedEventId]);
  const selectedNight = useMemo(() => eventNights.find((night) => Number(night.id) === Number(selectedNightId)), [eventNights, selectedNightId]);
  const eventBars = useMemo(() => bars.filter((bar) => Number(bar.event_id) === Number(selectedEventId)), [bars, selectedEventId]);
  const eventTimeline = useMemo(() => eventNights.filter((night) => Number(night.event_id) === Number(selectedEventId)).sort((a, b) => a.night_number - b.night_number), [eventNights, selectedEventId]);
  const eventReports = useMemo(() => pdfReports.filter((report) => Number(report.event_id) === Number(selectedEventId)), [pdfReports, selectedEventId]);
  const nightReports = useMemo(() => pdfReports.filter((report) => Number(report.event_night_id) === Number(selectedNightId)), [pdfReports, selectedNightId]);
  const closingCashEmployees = useMemo(() => {
    if (!selectedNight || !forms.closingCash.bar_id) return [];
    const assignedIds = new Set(
      nightAssignments
        .filter((assignment) => Number(assignment.event_night_id) === Number(selectedNight.id) && Number(assignment.bar_id) === Number(forms.closingCash.bar_id))
        .map((assignment) => Number(assignment.user_id)),
    );
    return employees.filter((employee) => assignedIds.has(Number(employee.id)));
  }, [employees, forms.closingCash.bar_id, nightAssignments, selectedNight]);
  const closingStockProducts = useMemo(() => {
    if (!selectedNight || !forms.closingStock.bar_id) return [];
    const allocatedProductIds = new Set(
      stock
        .filter((item) => Number(item.event_night_id) === Number(selectedNight.id) && Number(item.bar_id) === Number(forms.closingStock.bar_id))
        .map((item) => Number(item.product_id)),
    );
    return products.filter((product) => allocatedProductIds.has(Number(product.id)));
  }, [forms.closingStock.bar_id, products, selectedNight, stock]);
  const previousNightClosed = eventTimeline.length === 0 || eventTimeline[eventTimeline.length - 1]?.status === 'closed';
  const plannedNights = Number(selectedEvent?.total_nights_planned || selectedEvent?.total_nights || 0);
  const allBarsClosedForNight = selectedNight && eventBars.length > 0 && eventBars.every((bar) => barSummaries.some((summary) => Number(summary.event_night_id) === Number(selectedNight.id) && Number(summary.bar_id) === Number(bar.id) && summary.is_closed));
  const canBeginNight = selectedEvent && selectedEvent.status !== 'closed' && !eventTimeline.some((night) => night.status === 'active') && previousNightClosed && eventTimeline.length < plannedNights;
  const canCloseEvent = selectedEvent && selectedEvent.status !== 'closed' && eventTimeline.length >= plannedNights && eventTimeline.every((night) => night.status === 'closed');
  const eventLocked = selectedEvent?.status === 'closed';
  const nightLocked = eventLocked || selectedNight?.status === 'closed';

  async function loadAll() {
    const [userRes, eventRes, nightRes, barRes, categoryRes, productRes, eventStockRes, stockRes, assignmentRes, cashRes, summaryRes, snapshotRes, pdfRes, auditRes] = await Promise.all([
      api.get('/admin/users'),
      api.get('/admin/events'),
      api.get('/admin/event-nights'),
      api.get('/admin/bars'),
      api.get('/admin/product-categories'),
      api.get('/admin/products'),
      api.get('/admin/event-stock'),
      api.get('/admin/stock'),
      api.get('/admin/night-assignments'),
      api.get('/admin/bartender-cash'),
      api.get('/admin/bar-night-summaries'),
      api.get('/admin/profit-snapshots'),
      api.get('/admin/pdf-reports'),
      api.get('/admin/audit-logs'),
    ]);
    setUsers(userRes.data);
    setEvents(eventRes.data);
    setEventNights(nightRes.data);
    setBars(barRes.data);
    setCategories(categoryRes.data);
    setProducts(productRes.data);
    setEventStock(eventStockRes.data);
    setStock(stockRes.data);
    setNightAssignments(assignmentRes.data);
    setBartenderCash(cashRes.data);
    setBarSummaries(summaryRes.data);
    setSnapshots(snapshotRes.data);
    setPdfReports(pdfRes.data);
    setAuditLogs(auditRes.data);
  }

  useEffect(() => {
    loadAll().catch((err) => setMessage(formatApiError(err, 'Impossible de charger les données admin.')));
  }, []);

  function setForm(name, field, value) {
    setForms((current) => ({ ...current, [name]: { ...current[name], [field]: value } }));
  }

  function setClosingCashBar(value) {
    setForms((current) => ({
      ...current,
      closingCash: {
        ...current.closingCash,
        bar_id: value,
        user_id: '',
      },
    }));
  }

  function setClosingStockBar(value) {
    setForms((current) => ({
      ...current,
      closingStock: {
        ...current.closingStock,
        bar_id: value,
        product_id: '',
      },
    }));
  }

  async function submit(name, endpoint, payload, resetValue, onSuccess) {
    setMessage('');
    try {
      const { data } = await api.post(endpoint, payload);
      setForms((current) => ({ ...current, [name]: resetValue }));
      await loadAll();
      if (onSuccess) onSuccess(data);
      setMessage('Enregistré avec succès.');
    } catch (err) {
      setMessage(formatApiError(err, 'Échec de l’enregistrement.'));
    }
  }

  async function beginNight(event) {
    event.preventDefault();
    await submit('beginNight', '/admin/event-nights', { event_id: selectedEventId, date: forms.beginNight.date }, blankBeginNight, (night) => setSelectedNightId(night.id));
  }

  async function saveNightStaff(event) {
    event.preventDefault();
    const assignments = [];
    if (forms.nightStaff.responsible_user_id) assignments.push({ user_id: forms.nightStaff.responsible_user_id, role: 'responsible', salary_amount: forms.nightStaff.salary_amount || '0' });
    await submit('nightStaff', '/admin/night-assignments', { event_night_id: selectedNightId, bar_id: forms.nightStaff.bar_id, assignments }, blankNightStaff);
  }

  async function randomStaffForBar(event) {
    event.preventDefault();
    await submit('randomStaff', '/admin/night-assignments/random-bar', {
      event_night_id: selectedNightId,
      bar_id: forms.randomStaff.bar_id,
      employee_count: forms.randomStaff.employee_count,
      salary_amount: forms.randomStaff.salary_amount,
    }, blankRandomStaff);
  }

  async function saveOpeningStock(event) {
    event.preventDefault();
    await submit('openingStock', '/admin/opening-stock', {
      event_night_id: selectedNightId,
      bar_id: forms.openingStock.bar_id,
      items: [{
        product_id: forms.openingStock.product_id,
        qty_opening: forms.openingStock.qty_opening,
        selling_price: forms.openingStock.selling_price,
      }],
    }, blankOpeningStock);
  }

  async function saveClosingStock(event) {
    event.preventDefault();
    await submit('closingStock', '/admin/end-of-night', {
      event_night_id: selectedNightId,
      bar_id: forms.closingStock.bar_id,
      stock_items: [{ product_id: forms.closingStock.product_id, qty_closing: forms.closingStock.qty_closing }],
      bartender_cash: [],
      close_bar: false,
    }, blankClosingStock);
  }

  async function saveClosingCash(event) {
    event.preventDefault();
    await submit('closingCash', '/admin/end-of-night', {
      event_night_id: selectedNightId,
      bar_id: forms.closingCash.bar_id,
      stock_items: [],
      bartender_cash: [{ user_id: forms.closingCash.user_id, cash_collected: forms.closingCash.cash_collected }],
      close_bar: false,
    }, blankClosingCash);
  }

  async function closeBar(event) {
    event.preventDefault();
    await submit('closeBar', '/admin/end-of-night', {
      event_night_id: selectedNightId,
      bar_id: forms.closeBar.bar_id,
      stock_items: [],
      bartender_cash: [],
      close_bar: true,
    }, blankCloseBar);
  }

  async function closeNight() {
    if (!allBarsClosedForNight) {
      setMessage('Clôturez chaque bar avant de clôturer la nuit.');
      return;
    }
    try {
      await api.post(`/admin/event-nights/${selectedNightId}/close`);
      await loadAll();
      setMessage('Nuit clôturée et rapports PDF générés.');
    } catch (err) {
      setMessage(formatApiError(err, 'Échec de la clôture de la nuit.'));
    }
  }

  async function closeEvent() {
    if (!canCloseEvent) {
      setMessage('Toutes les nuits prévues doivent être clôturées avant l’événement.');
      return;
    }
    try {
      await api.post(`/admin/events/${selectedEventId}/close`);
      await loadAll();
      setMessage('Événement clôturé et rapport PDF généré.');
    } catch (err) {
      setMessage(formatApiError(err, 'Échec de la clôture de l’événement.'));
    }
  }

  async function downloadReport(reportId) {
    const response = await api.get(`/admin/pdf-reports/${reportId}`, { responseType: 'blob' });
    const disposition = response.headers['content-disposition'] || '';
    const filename = disposition.match(/filename="(.+)"/)?.[1] || 'FestivaPro_Report.pdf';
    const url = URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  }

  if (!pageMeta) return <Navigate to="/admin/events" replace />;

  return (
    <main className="workspace">
      <div className="page-title">
        <div>
          <h1>{pageMeta[0]}</h1>
          <p>{pageMeta[1]}</p>
        </div>
        {message && <div className="status-pill">{message}</div>}
      </div>

      {activePage === 'events' && (
        <div className="resource-grid table-page">
          {!selectedEvent && <EventsRoot events={events} nights={eventNights} summaries={barSummaries} snapshots={snapshots} forms={forms} setForm={setForm} submit={submit} setSelectedEventId={setSelectedEventId} />}
          {selectedEvent && !selectedNight && (
            <ResourcePanel title={`${selectedEvent.name} / ${selectedEvent.location}`} icon={<CalendarDays size={18} />}>
              <div className="inline-tools">
                <button className="secondary-button" type="button" onClick={() => setSelectedEventId('')}>Événements</button>
                {!eventLocked && <button className="primary-button" type="button" onClick={closeEvent}>Clôturer l’événement</button>}
              </div>
              {eventLocked && <div className="status-pill">Événement clôturé : lecture seule.</div>}
              <h3>Bars</h3>
              {!eventLocked && <form className="compact-form" onSubmit={(event) => { event.preventDefault(); submit('bar', '/admin/bars', { event_id: selectedEventId, ...forms.bar }, blankBar); }}>
                <FormField label="Nom du bar" help="Physical bar or zone inside this event.">
                  <input placeholder="Exemple : Bar VIP" value={forms.bar.name} onChange={(e) => setForm('bar', 'name', e.target.value)} required />
                </FormField>
                <button className="primary-button" type="submit"><Plus size={16} />Ajouter le bar</button>
              </form>}
              <div className="card-grid">
                {eventBars.map((bar) => <EventBarCard key={bar.id} bar={bar} users={users} nights={eventTimeline} assignments={nightAssignments} summaries={barSummaries} />)}
              </div>
              <h3>Nuits</h3>
              {canBeginNight && (
                <form className="compact-form" onSubmit={beginNight}>
                  <FormField label="Date de la nuit" help="Calendar date for the night you are starting.">
                    <input value={forms.beginNight.date} onChange={(e) => setForm('beginNight', 'date', e.target.value)} required type="date" />
                  </FormField>
                  <button className="primary-button" type="submit"><Moon size={16} />Commencer la nuit</button>
                </form>
              )}
              <DataTable columns={['Nuit', 'Date', 'Statut', 'Cash', 'Écart', '']} rows={eventTimeline.map((night) => {
                const sums = barSummaries.filter((item) => item.event_night_id === night.id);
                return [`Nuit ${night.night_number}`, night.date, statusLabel(night.status), money(sum(sums, 'total_cash_collected')), money(sum(sums, 'cash_discrepancy')), <button className="secondary-button" type="button" onClick={() => setSelectedNightId(night.id)}>Ouvrir</button>];
              })} />
              <h3>Rapports</h3>
              <ReportList reports={eventReports} onDownload={downloadReport} />
            </ResourcePanel>
          )}
          {selectedEvent && selectedNight && (
            <ResourcePanel title={`${selectedEvent.name} / Nuit ${selectedNight.night_number}`} icon={<Moon size={18} />}>
              <div className="inline-tools">
                <button className="secondary-button" type="button" onClick={() => setSelectedNightId('')}>Événement</button>
                {!nightLocked && <button className="primary-button" type="button" onClick={closeNight}>Clôturer la nuit</button>}
              </div>
              {nightLocked && <div className="status-pill">Nuit en lecture seule.</div>}
              <div className="card-grid">
                {eventBars.map((bar) => <NightBarPanel key={bar.id} bar={bar} users={users} products={products} stock={stock} assignments={nightAssignments} summaries={barSummaries} cash={bartenderCash} nightId={selectedNight.id} />)}
              </div>
              {!nightLocked && <>
              <h3>Affecter le personnel</h3>
              <form className="compact-form" onSubmit={saveNightStaff}>
                <FormField label="Bar" help="Bar receiving this night-specific staff assignment.">
                  <Select value={forms.nightStaff.bar_id} onChange={(value) => setForm('nightStaff', 'bar_id', value)} options={eventBars} label="Sélectionner un bar" />
                </FormField>
                <FormField label="Responsable de la nuit" help="Person responsible for this bar tonight only; can change every night.">
                  <Select value={forms.nightStaff.responsible_user_id} onChange={(value) => setForm('nightStaff', 'responsible_user_id', value)} options={employees} label="Sélectionner le responsable" />
                </FormField>
                <FormField label="Salaire de service" help="Salary paid to the selected staff member for this night.">
                  <input placeholder="MAD" value={forms.nightStaff.salary_amount} onChange={(e) => setForm('nightStaff', 'salary_amount', e.target.value)} type="number" />
                </FormField>
                <button className="primary-button" type="submit"><ClipboardList size={16} />Enregistrer</button>
              </form>
              <form className="compact-form" onSubmit={randomStaffForBar}>
                <FormField label="Bar" help="Bar that should receive random bartenders tonight.">
                  <Select value={forms.randomStaff.bar_id} onChange={(value) => setForm('randomStaff', 'bar_id', value)} options={eventBars} label="Sélectionner un bar" />
                </FormField>
                <FormField label="Nombre d’employés" help="Number of available employees to randomly assign to this bar.">
                  <input placeholder="Exemple : 3" value={forms.randomStaff.employee_count} onChange={(e) => setForm('randomStaff', 'employee_count', e.target.value)} min="1" type="number" />
                </FormField>
                <FormField label="Salaire par employé" help="Same shift salary applied to every randomly assigned bartender.">
                  <input placeholder="MAD" value={forms.randomStaff.salary_amount} onChange={(e) => setForm('randomStaff', 'salary_amount', e.target.value)} min="0" type="number" />
                </FormField>
                <button className="secondary-button" type="submit"><Shuffle size={16} />Affecter aléatoirement</button>
              </form>
              <h3>Stock d’ouverture</h3>
              <form className="compact-form" onSubmit={saveOpeningStock}>
                <FormField label="Bar" help="Bar receiving this product for the selected night.">
                  <Select value={forms.openingStock.bar_id} onChange={(value) => setForm('openingStock', 'bar_id', value)} options={eventBars} label="Sélectionner un bar" />
                </FormField>
                <FormField label="Produit" help="Product placed into the bar stock.">
                  <Select value={forms.openingStock.product_id} onChange={(value) => setForm('openingStock', 'product_id', value)} options={products} label="Sélectionner un produit" />
                </FormField>
                <FormField label="Quantité" help="Units placed in the bar before opening.">
                  <input placeholder="Unités" value={forms.openingStock.qty_opening} onChange={(e) => setForm('openingStock', 'qty_opening', e.target.value)} type="number" />
                </FormField>
                <FormField label="Prix de vente" help="Customer price per unit. Used for expected cash.">
                  <input placeholder="MAD" value={forms.openingStock.selling_price} onChange={(e) => setForm('openingStock', 'selling_price', e.target.value)} type="number" />
                </FormField>
                <button className="primary-button" type="submit"><Plus size={16} />Enregistrer le stock</button>
              </form>
              <h3>Fin de nuit par bar</h3>
              <form className="compact-form" onSubmit={saveClosingStock}>
                <FormField label="Bar" help="Bar receiving the remaining stock count.">
                  <Select value={forms.closingStock.bar_id} onChange={setClosingStockBar} options={eventBars} label="Sélectionner un bar" />
                </FormField>
                <FormField label="Produit" help="Product being physically counted after the night.">
                  <Select value={forms.closingStock.product_id} onChange={(value) => setForm('closingStock', 'product_id', value)} options={closingStockProducts} label={forms.closingStock.bar_id ? 'Sélectionner un produit ouvert' : 'Sélectionner un bar d’abord'} />
                </FormField>
                <FormField label="Quantité restante" help="Units left in the bar after service ends.">
                  <input placeholder="Unités restantes" value={forms.closingStock.qty_closing} onChange={(e) => setForm('closingStock', 'qty_closing', e.target.value)} type="number" />
                </FormField>
                <button className="secondary-button" type="submit"><ReceiptText size={16} />Enregistrer stock</button>
              </form>
              <form className="compact-form" onSubmit={saveClosingCash}>
                <FormField label="Bar" help="Bar receiving the employee cash entry.">
                  <Select value={forms.closingCash.bar_id} onChange={setClosingCashBar} options={eventBars} label="Sélectionner un bar" />
                </FormField>
                <FormField label="Employé" help="Employee handing in cash. Phone is shown for confirmation.">
                  <Select value={forms.closingCash.user_id} onChange={(value) => setForm('closingCash', 'user_id', value)} options={closingCashEmployees} label={forms.closingCash.bar_id ? 'Sélectionner un employé affecté' : 'Sélectionner un bar d’abord'} />
                </FormField>
                <FormField label="Cash encaissé" help="Actual MAD cash this bartender handed in.">
                  <input placeholder="MAD" value={forms.closingCash.cash_collected} onChange={(e) => setForm('closingCash', 'cash_collected', e.target.value)} type="number" />
                </FormField>
                <button className="secondary-button" type="submit"><ReceiptText size={16} />Enregistrer cash</button>
              </form>
              <form className="compact-form" onSubmit={closeBar}>
                <FormField label="Bar" help="Locks this bar after all remaining stock and employee cash entries are saved.">
                  <Select value={forms.closeBar.bar_id} onChange={(value) => setForm('closeBar', 'bar_id', value)} options={eventBars} label="Sélectionner un bar" />
                </FormField>
                <button className="primary-button" type="submit"><ReceiptText size={16} />Clôturer le bar</button>
              </form>
              </>}
              <h3>Rapports de nuit</h3>
              <ReportList reports={nightReports} onDownload={downloadReport} />
            </ResourcePanel>
          )}
        </div>
      )}

      {activePage !== 'events' && <UtilityPages activePage={activePage} users={users} employees={employees} events={events} categories={categories} products={products} eventStock={eventStock} pdfReports={pdfReports} auditLogs={auditLogs} forms={forms} setForm={setForm} submit={submit} onDownload={downloadReport} />}
    </main>
  );
}

function EventsRoot({ events, nights, summaries, snapshots, forms, setForm, submit, setSelectedEventId }) {
  return (
    <ResourcePanel title="Tous les événements" icon={<CalendarDays size={18} />}>
      <form className="compact-form" onSubmit={(event) => { event.preventDefault(); submit('event', '/admin/events', forms.event, blankEvent, (created) => setSelectedEventId(created.id)); }}>
        <FormField label="Nom de l’événement" help="Festival or event name shown on dashboards and PDF reports.">
          <input placeholder="Exemple : Summer Fest" value={forms.event.name} onChange={(e) => setForm('event', 'name', e.target.value)} required />
        </FormField>
        <FormField label="Ville" help="Moroccan city where the event takes place.">
          <input placeholder="Ville, Maroc" value={forms.event.location} onChange={(e) => setForm('event', 'location', e.target.value)} required />
        </FormField>
        <FormField label="Date de début" help="Date used as the event start and default first night reference.">
          <input value={forms.event.start_date} onChange={(e) => setForm('event', 'start_date', e.target.value)} required type="date" />
        </FormField>
        <FormField label="Nuits prévues" help="Maximum number of nights this event should contain.">
          <input placeholder="Nuits prévues" value={forms.event.total_nights_planned} onChange={(e) => setForm('event', 'total_nights_planned', e.target.value)} min="1" type="number" />
        </FormField>
        <button className="primary-button" type="submit"><Plus size={16} />Créer l’événement</button>
      </form>
      <div className="card-grid">
        {events.map((event) => {
          const eventNights = nights.filter((night) => night.event_id === event.id);
          const closedNights = eventNights.filter((night) => night.status === 'closed').length;
          const latestSnapshot = snapshots.find((snapshot) => snapshot.event_id === event.id && snapshot.snapshot_level === 'event');
          return (
            <button className="event-card" key={event.id} type="button" onClick={() => setSelectedEventId(event.id)}>
              <strong>{event.name}</strong>
              <span>{event.location}</span>
              <span>{dateRange(eventNights, event.start_date)}</span>
              <span className={`status-badge ${event.status}`}>{statusLabel(event.status)}</span>
              <span>{event.total_nights_planned || event.total_nights} nuits prévues</span>
              <span>{closedNights} clôturées / {money(latestSnapshot?.actual_revenue)} cash / {money(latestSnapshot?.net_profit)} net</span>
            </button>
          );
        })}
        {events.length === 0 && <p className="muted">Aucun événement pour le moment.</p>}
      </div>
    </ResourcePanel>
  );
}

function EventBarCard({ bar, users, nights, assignments, summaries }) {
  const activeNight = nights.find((night) => night.status === 'active');
  const currentNight = activeNight || [...nights].reverse().find(Boolean);
  const nightAssignments = currentNight ? assignments.filter((item) => Number(item.event_night_id) === Number(currentNight.id) && Number(item.bar_id) === Number(bar.id)) : [];
  const currentSummary = currentNight ? summaries.find((item) => Number(item.event_night_id) === Number(currentNight.id) && Number(item.bar_id) === Number(bar.id)) : null;
  const responsible = nightAssignments.find((item) => item.role === 'responsible');
  const bartenderCount = nightAssignments.filter((item) => item.role === 'bartender').length;
  const status = currentSummary?.is_closed ? 'BAR CLÔTURÉ' : nightAssignments.length ? 'EN COURS' : 'EN ATTENTE';
  return (
    <div className="drill-card">
      <strong>{bar.name}</strong>
      <span>Responsable de nuit : {responsible ? userLabel(users, responsible.user_id) : '-'}</span>
      <span>{bartenderCount} employés affectés</span>
      <span>{currentNight ? `Nuit ${currentNight.night_number} : ${status}` : 'Aucune nuit commencée'}</span>
    </div>
  );
}

function NightBarPanel({ bar, users, products, stock, assignments, summaries, cash, nightId }) {
  const barAssignments = assignments.filter((item) => item.event_night_id === nightId && item.bar_id === bar.id);
  const barStock = stock.filter((item) => item.event_night_id === nightId && item.bar_id === bar.id);
  const summary = summaries.find((item) => item.event_night_id === nightId && item.bar_id === bar.id);
  const ready = barAssignments.length > 0 && barStock.length > 0;
  return (
    <div className="drill-card">
      <strong>{bar.name}</strong>
      <span>{ready ? 'PRÊT' : 'CONFIGURATION EN ATTENTE'}</span>
      <span>Responsable ce soir : {barAssignments.filter((item) => item.role === 'responsible').map((item) => userLabel(users, item.user_id)).join(', ') || '-'}</span>
      <span>Employés : {barAssignments.filter((item) => item.role === 'bartender').map((item) => userLabel(users, item.user_id)).join(', ') || '-'}</span>
      <span>Objectif : {money(barStock.reduce((total, row) => total + ((Number(row.qty_opening || 0) + Number(row.qty_top_up || 0)) * Number(row.selling_price || 0)), 0))}</span>
      {summary && <span className={Number(summary.cash_discrepancy) === 0 ? 'positive' : Number(summary.cash_discrepancy) > 0 ? 'negative' : 'warning'}>{Number(summary.cash_discrepancy) === 0 ? 'Équilibré' : Number(summary.cash_discrepancy) > 0 ? `Manquant ${money(summary.cash_discrepancy)}` : `Surplus ${money(Math.abs(Number(summary.cash_discrepancy)))}`}</span>}
      <DataTable columns={['Produit', 'Quantité départ', 'Restant', 'Utilisé', 'Vente']} rows={barStock.map((row) => [productName(products, row.product_id), Number(row.qty_opening || 0) + Number(row.qty_top_up || 0), row.qty_closing ?? '-', row.qty_used, money(row.selling_price)])} />
      <DataTable columns={['Employé', 'Cash']} rows={cash.filter((row) => row.event_night_id === nightId && row.bar_id === bar.id).map((row) => [userName(users, row.user_id), money(row.cash_collected)])} />
    </div>
  );
}

function UtilityPages({ activePage, users, employees, events, categories, products, eventStock, pdfReports, auditLogs, forms, setForm, submit, onDownload }) {
  if (activePage === 'users') {
    return (
      <ResourcePanel title="Utilisateurs" icon={<UsersRound size={18} />}>
        <form className="compact-form" onSubmit={(event) => { event.preventDefault(); submit('user', '/admin/users', forms.user, blankUser); }}>
          <FormField label="Nom complet"><input placeholder="Nom complet" value={forms.user.full_name} onChange={(e) => setForm('user', 'full_name', e.target.value)} required /></FormField>
          <FormField label="Email"><input placeholder="Email" value={forms.user.email} onChange={(e) => setForm('user', 'email', e.target.value)} required type="email" /></FormField>
          <FormField label="Téléphone"><input placeholder="Téléphone" value={forms.user.phone_number} onChange={(e) => setForm('user', 'phone_number', e.target.value)} /></FormField>
          <FormField label="Rôle"><select value={forms.user.role} onChange={(e) => setForm('user', 'role', e.target.value)}><option value="employee">Employé</option><option value="admin">Admin</option></select></FormField>
          <FormField label="Mot de passe"><input placeholder="Mot de passe" value={forms.user.password} onChange={(e) => setForm('user', 'password', e.target.value)} required type="password" /></FormField>
          <button className="primary-button" type="submit"><Plus size={16} />Ajouter</button>
        </form>
        <DataTable columns={['Nom', 'Rôle', 'Email', 'Téléphone']} rows={users.map((user) => [user.full_name, roleLabel(user.role), user.email, user.phone_number || '-'])} />
      </ResourcePanel>
    );
  }
  if (activePage === 'categories') {
    return (
      <ResourcePanel title="Catégories" icon={<FolderTree size={18} />}>
        <form className="compact-form" onSubmit={(event) => { event.preventDefault(); submit('category', '/admin/product-categories', forms.category, blankCategory); }}>
          <FormField label="Nom de catégorie"><input placeholder="Nom de catégorie" value={forms.category.name} onChange={(e) => setForm('category', 'name', e.target.value)} required /></FormField>
          <button className="primary-button" type="submit"><Plus size={16} />Ajouter</button>
        </form>
        <DataTable columns={['Catégorie']} rows={categories.map((category) => [category.name])} />
      </ResourcePanel>
    );
  }
  if (activePage === 'products') {
    return (
      <ResourcePanel title="Produits" icon={<Package size={18} />}>
        <form className="compact-form" onSubmit={(event) => { event.preventDefault(); submit('product', '/admin/products', forms.product, blankProduct); }}>
          <FormField label="Nom du produit"><input placeholder="Nom" value={forms.product.name} onChange={(e) => setForm('product', 'name', e.target.value)} required /></FormField>
          <FormField label="Catégorie"><Select value={forms.product.category_id} onChange={(value) => setForm('product', 'category_id', value)} options={categories} label="Sélectionner une catégorie" /></FormField>
          <FormField label="Unité"><select value={forms.product.unit} onChange={(e) => setForm('product', 'unit', e.target.value)}><option value="bottle">Bouteille</option><option value="can">Canette</option><option value="unit">Unité</option></select></FormField>
          <button className="primary-button" type="submit"><Plus size={16} />Ajouter</button>
        </form>
        <DataTable columns={['Produit', 'Catégorie', 'Unité']} rows={products.map((product) => [product.name, categoryName(categories, product.category_id), unitLabel(product.unit)])} />
      </ResourcePanel>
    );
  }
  if (activePage === 'event-stock') {
    return (
      <ResourcePanel title="Stock événement" icon={<BadgeDollarSign size={18} />}>
        <form className="compact-form" onSubmit={(event) => { event.preventDefault(); submit('eventStock', '/admin/event-stock', forms.eventStock, blankEventStock); }}>
          <FormField label="Événement"><Select value={forms.eventStock.event_id} onChange={(value) => setForm('eventStock', 'event_id', value)} options={events.filter((event) => event.status !== 'closed')} label="Sélectionner un événement" /></FormField>
          <FormField label="Produit"><Select value={forms.eventStock.product_id} onChange={(value) => setForm('eventStock', 'product_id', value)} options={products} label="Sélectionner un produit" /></FormField>
          <FormField label="Quantité achetée"><input placeholder="Quantité achetée" value={forms.eventStock.total_qty_purchased} onChange={(e) => setForm('eventStock', 'total_qty_purchased', e.target.value)} type="number" /></FormField>
          <FormField label="Prix d’achat"><input placeholder="MAD" value={forms.eventStock.bought_price} onChange={(e) => setForm('eventStock', 'bought_price', e.target.value)} type="number" /></FormField>
          <FormField label="Prix de vente"><input placeholder="MAD" value={forms.eventStock.selling_price} onChange={(e) => setForm('eventStock', 'selling_price', e.target.value)} type="number" /></FormField>
          <button className="primary-button" type="submit"><Plus size={16} />Définir</button>
        </form>
        <DataTable columns={['Événement', 'Produit', 'Acheté', 'Vente']} rows={eventStock.map((row) => [eventName(events, row.event_id), productName(products, row.product_id), row.total_qty_purchased, money(row.selling_price)])} />
      </ResourcePanel>
    );
  }
  if (activePage === 'audit') return <ResourcePanel title="Journal d’audit" icon={<ReceiptText size={18} />}><DataTable columns={['Date', 'Action', 'Entité']} rows={auditLogs.map((log) => [new Date(log.created_at).toLocaleString(), auditActionLabel(log.action), `${entityLabel(log.entity_type)} #${log.entity_id || '-'}`])} /></ResourcePanel>;
  if (activePage === 'reports') {
    return (
      <ResourcePanel title="Rapports" icon={<Download size={18} />}>
        <DataTable columns={['Événement', 'Type', 'Fichier', 'Généré', '']} rows={pdfReports.map((report) => [
          eventName(events, report.event_id),
          reportTypeLabel(report.report_type),
          report.filename,
          new Date(report.generated_at).toLocaleString(),
          <button className="secondary-button" type="button" onClick={() => onDownload(report.id)}><Download size={16} />PDF</button>,
        ])} />
      </ResourcePanel>
    );
  }
  return null;
}

function ReportList({ reports, onDownload }) {
  return <DataTable columns={['Type', 'Fichier', 'Généré', '']} rows={reports.map((report) => [reportTypeLabel(report.report_type), report.filename, new Date(report.generated_at).toLocaleString(), <button className="secondary-button" type="button" onClick={() => onDownload(report.id)}><Download size={16} />PDF</button>])} />;
}

function FormField({ label, children }) {
  return (
    <label className="field-help">
      <span>{label}</span>
      {children}
    </label>
  );
}

function Select({ value, onChange, options, label }) {
  return <select value={value} onChange={(event) => onChange(event.target.value)} required><option value="">{label}</option>{options.map((option) => <option key={option.id} value={option.id}>{optionLabel(option)}</option>)}</select>;
}

function DataTable({ columns, rows }) {
  return <div className="table-wrap"><table><thead><tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr></thead><tbody>{rows.length === 0 ? <tr><td colSpan={columns.length}>Aucun enregistrement pour le moment.</td></tr> : rows.map((row, index) => <tr key={index}>{row.map((cell, cellIndex) => <td key={cellIndex}>{cell}</td>)}</tr>)}</tbody></table></div>;
}

function sum(rows, field) {
  return rows.reduce((total, row) => total + Number(row[field] || 0), 0);
}

function dateRange(nights, fallback) {
  if (!nights.length) return fallback;
  const sorted = [...nights].sort((a, b) => a.night_number - b.night_number);
  return `${sorted[0].date} → ${sorted[sorted.length - 1].date}`;
}

function eventName(events, id) {
  return events.find((event) => Number(event.id) === Number(id))?.name || `Événement ${id}`;
}

function categoryName(categories, id) {
  return categories.find((category) => Number(category.id) === Number(id))?.name || `Catégorie ${id}`;
}

function productName(products, id) {
  return products.find((product) => Number(product.id) === Number(id))?.name || `Produit ${id}`;
}

function userName(users, id) {
  return users.find((user) => Number(user.id) === Number(id))?.full_name || `Utilisateur ${id}`;
}

function userLabel(users, id) {
  const user = users.find((item) => Number(item.id) === Number(id));
  if (!user) return `Utilisateur ${id}`;
  return `${user.full_name}${user.phone_number ? ` / ${user.phone_number}` : ''}`;
}

function optionLabel(option) {
  const base = option.name || option.full_name;
  return option.phone_number ? `${base} / ${option.phone_number}` : base;
}

function statusLabel(status) {
  return {
    upcoming: 'À venir',
    active: 'Actif',
    closed: 'Clôturé',
  }[status] || status;
}

function roleLabel(role) {
  return {
    admin: 'Admin',
    employee: 'Employé',
    responsible: 'Responsable',
    bartender: 'Employé',
  }[role] || role;
}

function unitLabel(unit) {
  return {
    bottle: 'Bouteille',
    can: 'Canette',
    unit: 'Unité',
  }[unit] || unit;
}

function reportTypeLabel(type) {
  return {
    bar_night: 'Bar / nuit',
    night: 'Nuit complète',
    event: 'Événement complet',
  }[type] || type;
}

function auditActionLabel(action) {
  return {
    create_event: 'Création événement',
    close_event: 'Clôture événement',
    close_night: 'Clôture nuit',
    create_bar: 'Création bar',
    edit_opening_stock: 'Stock d’ouverture',
    submit_bar_end_of_night: 'Fin de nuit bar',
    seed_create_event: 'Seed événement',
    seed_create_bar: 'Seed bar',
    seed_event_stock: 'Seed stock',
    seed_open_night: 'Seed ouverture nuit',
    seed_close_bar: 'Seed clôture bar',
    seed_close_night: 'Seed clôture nuit',
    seed_close_event: 'Seed clôture événement',
  }[action] || action;
}

function entityLabel(entity) {
  return {
    events: 'Événements',
    event_nights: 'Nuits',
    bars: 'Bars',
    event_stock: 'Stock événement',
    event_salaries: 'Salaires',
  }[entity] || entity;
}
