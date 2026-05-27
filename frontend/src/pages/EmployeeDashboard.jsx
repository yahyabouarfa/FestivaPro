import { useEffect, useState } from 'react';
import { BadgeDollarSign, CalendarDays, ClipboardList, Store, UserRound, WalletCards } from 'lucide-react';
import { api } from '../api/client.js';
import { formatApiError } from '../api/errors.js';

function money(value) {
  return Number(value || 0).toLocaleString(undefined, { style: 'currency', currency: 'MAD' });
}

export default function EmployeeDashboard() {
  const [dashboard, setDashboard] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    api
      .get('/employee/dashboard')
      .then(({ data }) => setDashboard(data))
      .catch((err) => setError(formatApiError(err, 'Impossible de charger le tableau de bord.')));
  }, []);

  if (error) return <main className="workspace"><div className="error-message">{error}</div></main>;
  if (!dashboard) return <div className="loading">Chargement du tableau de bord...</div>;

  return (
    <main className="workspace employee-workspace">
      <div className="page-title">
        <div>
          <h1>Tableau de bord employé</h1>
          <p>Votre bar affecté, votre salaire de service, les prix actuels et votre contribution de fin de nuit.</p>
        </div>
      </div>

      {!dashboard.assignment ? (
        <section className="empty-state">
          <ClipboardList size={38} />
          <h2>Aucune affectation</h2>
          <p>Un administrateur ne vous a pas encore affecté à un bar pour l’événement en cours.</p>
        </section>
      ) : (
        <>
          {dashboard.reassignment_notice && <div className="status-pill">{dashboard.reassignment_notice}</div>}
          <section className="employee-summary">
            <div>
              <Store size={22} />
              <span>Bar affecté</span>
              <strong>{dashboard.bar?.name}</strong>
              <small>{dashboard.responsible_person || 'Responsable non défini'}{dashboard.responsible_phone ? ` / ${dashboard.responsible_phone}` : ''}</small>
            </div>
            <div>
              <WalletCards size={22} />
              <span>Salaire de service</span>
              <strong>{money(dashboard.assignment.salary_amount)}</strong>
              <small>{roleLabel(dashboard.assignment_role)}</small>
            </div>
            <div>
              <BadgeDollarSign size={22} />
              <span>Votre contribution</span>
              <strong>{money(dashboard.contribution)}</strong>
              <small>{dashboard.bar_closed ? `${dashboard.units_sold} unités / ${dashboard.contribution_pct}%` : 'Disponible après clôture du bar'}</small>
            </div>
            <div>
              <CalendarDays size={22} />
              <span>Nuit affectée</span>
              <strong>{dashboard.night ? `Nuit ${dashboard.night.night_number}` : '-'}</strong>
              <small>{dashboard.night?.date || '-'} / {statusLabel(dashboard.night?.status)}</small>
            </div>
            <div>
              <UserRound size={22} />
              <span>Affectation</span>
              <strong>{roleLabel(dashboard.assignment_role)}</strong>
              <small>{dashboard.event?.location || '-'} / total bar {money(dashboard.bar_total_cash)}</small>
            </div>
          </section>

          <section className="resource-panel">
            <div className="panel-heading">
              <h2><ClipboardList size={18} />Prix des produits</h2>
              <span className="muted">{dashboard.event?.name}</span>
            </div>
            <div className="price-list">
              {dashboard.prices.map((item) => (
                <div key={item.product_id} className="price-row">
                  <div>
                    <strong>{item.product_name}</strong>
                    <span>{item.category_name} / {item.unit}</span>
                  </div>
                  <b>{money(item.price)}</b>
                </div>
              ))}
            </div>
          </section>
        </>
      )}
    </main>
  );
}

function roleLabel(role) {
  return {
    responsible: 'Responsable',
    bartender: 'Barman',
  }[role] || role || '-';
}

function statusLabel(status) {
  return {
    upcoming: 'À venir',
    active: 'Active',
    closed: 'Clôturée',
  }[status] || status || '-';
}
