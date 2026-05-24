import { useState } from 'react';
import { Martini, ShieldCheck } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext.jsx';

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
      setError(err.response?.data?.detail || 'Unable to sign in.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-panel">
        <div className="login-mark">
          <Martini size={34} />
          <div>
            <h1>FestivaPro</h1>
            <p>Festival bar operations</p>
          </div>
        </div>
        <form className="form-grid" onSubmit={handleSubmit}>
          <label>
            Email
            <input value={email} onChange={(event) => setEmail(event.target.value)} required type="email" />
          </label>
          <label>
            Password
            <input value={password} onChange={(event) => setPassword(event.target.value)} required type="password" />
          </label>
          {error && <div className="error-message">{error}</div>}
          <button className="primary-button" disabled={submitting} type="submit">
            <ShieldCheck size={18} />
            {submitting ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
      </section>
    </main>
  );
}
