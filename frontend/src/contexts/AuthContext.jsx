import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, setSessionExpiredHandler, setTokens } from '../api/client.js';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem('user');
    return stored ? JSON.parse(stored) : null;
  });
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    setSessionExpiredHandler(() => {
      setUser(null);
      localStorage.removeItem('user');
      navigate('/login', { replace: true });
    });

    async function loadUser() {
      if (!localStorage.getItem('accessToken')) {
        setLoading(false);
        return;
      }
      try {
        const { data } = await api.get('/auth/me');
        setUser(data);
        localStorage.setItem('user', JSON.stringify(data));
      } catch {
        setUser(null);
      } finally {
        setLoading(false);
      }
    }
    loadUser();
  }, [navigate]);

  async function login(email, password) {
    const { data } = await api.post('/auth/login', { email, password });
    setTokens({ accessToken: data.access_token, refreshToken: data.refresh_token });
    setUser(data.user);
    localStorage.setItem('user', JSON.stringify(data.user));
    navigate(data.user.role === 'admin' ? '/admin' : '/employee', { replace: true });
  }

  async function logout() {
    const refreshToken = localStorage.getItem('refreshToken');
    if (refreshToken) {
      await api.post('/auth/logout', { refresh_token: refreshToken }).catch(() => {});
    }
    setTokens(null);
    setUser(null);
    localStorage.removeItem('user');
    navigate('/login', { replace: true });
  }

  const value = useMemo(() => ({ user, loading, login, logout }), [user, loading]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
