import React, { createContext, useState, useEffect } from 'react';
import { api } from '../api';

export const AuthContext = createContext({
  loggedIn: false,
  authReady: false,
  authEnabled: true,
  authConfigured: true,
  login: async () => ({}),
  logout: async () => {},
});

export function AuthProvider({ children }){
  const [loggedIn, setLoggedIn] = useState(false);
  const [authReady, setAuthReady] = useState(false);
  const [authEnabled, setAuthEnabled] = useState(true);
  const [authConfigured, setAuthConfigured] = useState(true);

  // Sync UI state with backend session (cookie)
  useEffect(() => {
    let active = true;
    api.get('/api/auth/me')
      .then((res) => {
        if (!active) return;
        const enabled = !!res?.data?.enabled;
        const configured = res?.data?.configured !== undefined ? !!res?.data?.configured : true;
        const authenticated = !!res?.data?.authenticated;

        setAuthEnabled(enabled);
        setAuthConfigured(configured);
        setLoggedIn(enabled ? authenticated : true);
        setAuthReady(true);
      })
      .catch(() => {
        if (!active) return;
        // Backend unreachable -> default to logged out (secure-by-default)
        setLoggedIn(false);
        setAuthReady(true);
      });
    return () => { active = false; };
  }, []);

  async function login(password){
    try {
      const res = await api.post('/api/auth/login', { password });
      if (res && res.data && res.data.ok) {
        setLoggedIn(true);
        setAuthReady(true);
        return { ok: true };
      }
      return { ok: false, message: 'Invalid password' };
    } catch (err) {
      const code = err?.response?.status;
      if (code === 401) return { ok: false, message: 'Invalid password' };
      const detail = err?.response?.data?.detail;
      if (detail) return { ok: false, message: String(detail) };
      return { ok: false, message: 'Login failed' };
    }
  }

  async function logout(){
    try { await api.post('/api/auth/logout'); } catch(e){}
    setLoggedIn(false);
    setAuthReady(true);

    // Clear any client-side stored state that could cause UI bypass.
    try{ sessionStorage.clear(); }catch(e){}
    try{ localStorage.clear(); }catch(e){}

    // Best-effort clear of non-HttpOnly cookies (HttpOnly session cookie is cleared server-side).
    try{
      document.cookie.split(';').forEach((c) => {
        const eqPos = c.indexOf('=');
        const name = (eqPos > -1 ? c.substr(0, eqPos) : c).trim();
        if (!name) return;
        document.cookie = `${name}=; Max-Age=0; path=/`;
      });
    }catch(e){}
  }

  return (
    <AuthContext.Provider value={{ loggedIn, authReady, authEnabled, authConfigured, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
