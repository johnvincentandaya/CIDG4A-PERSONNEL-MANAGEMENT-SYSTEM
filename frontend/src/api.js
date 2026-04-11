import axios from 'axios';

// Configure API base URL for dev/prod.
// - Dev: use same-origin/proxy by default, or REACT_APP_API_BASE override
// - Prod (single-link): use same origin (FastAPI serves frontend + /api)
// - Or override with REACT_APP_API_BASE (e.g. "http://192.168.1.50:8000")
let defaultBase = '';
if (typeof window !== 'undefined') {
  // In development, default to proxy (empty base). In production, use same-origin.
  if (process.env.NODE_ENV === 'development') {
    defaultBase = (process.env.REACT_APP_API_BASE && process.env.REACT_APP_API_BASE.replace(/\/$/, '')) || '';
  } else {
    defaultBase = '';
  }
}

export const API_BASE = (process.env.REACT_APP_API_BASE || defaultBase).replace(/\/$/, '');

export const api = axios.create({
  baseURL: API_BASE,
});

export function absolutizePath(path) {
  if (!path) return null;
  const p = String(path).replace(/\\\\/g, '/').replace(/\\/g, '/');
  const idx = p.indexOf('uploads/');
  const rel = idx >= 0 ? p.slice(idx) : p.replace(/^\//, '');
  const prefix = API_BASE ? API_BASE : '';
  return `${prefix}/${rel}`.replace(/([^:]\/)\/+/g, '$1');
}

