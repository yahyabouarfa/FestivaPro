import { useState } from 'react';
import { ShieldCheck } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext.jsx';
import { formatApiError } from '../api/errors.js';

const demoCredentials = [
  { role: 'Admin', email: 'admin@festivapro.local', password: 'password' },
  { role: 'Employé', email: 'seed.yassine@festivapro.local', password: 'password' },
];

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      await login(email, password);
    } catch (err) {
      setError(formatApiError(err, 'Connexion impossible.'));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-panel">
        <div className="login-mark">
          <img alt="Logo FestivaPro" src="/festivaprologo.png" />
          <div>
            <h1>FestivaPro</h1>
            <p>Gestion des bars de festival</p>
          </div>
        </div>
        <form className="form-grid" onSubmit={handleSubmit}>
          <label>
            Email
            <input value={email} onChange={(event) => setEmail(event.target.value)} required type="email" />
          </label>
          <label>
            Mot de passe
            <input value={password} onChange={(event) => setPassword(event.target.value)} required type="password" />
          </label>
          {error && <div className="error-message">{error}</div>}
          <button className="primary-button" disabled={submitting} type="submit">
            <ShieldCheck size={18} />
            {submitting ? 'Connexion...' : 'Se connecter'}
          </button>
        </form>
        <div className="login-credentials">
          <strong>Comptes de démonstration</strong>
          {demoCredentials.map((item) => (
            <button
              className="credential-row"
              key={item.email}
              onClick={() => {
                setEmail(item.email);
                setPassword(item.password);
              }}
              type="button"
            >
              <span>{item.role}</span>
              <code>{item.email}</code>
              <small>{item.password}</small>
            </button>
          ))}
        </div>
      </section>
    </main>
  );
}
