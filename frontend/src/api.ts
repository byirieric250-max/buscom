const configuredApiBaseUrl = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
const API_BASE_URL = configuredApiBaseUrl ||
  (import.meta.env.PROD ? 'https://buscom-backend.onrender.com' : '');

export function apiUrl(path: string): string {
  return `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;
}
