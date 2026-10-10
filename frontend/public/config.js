// Runtime environment configuration for PillSync frontend
// When deployed, window.VITE_API_URL can be set via environment variable or falls back to live Render backend.
window.VITE_API_URL =
  window.VITE_API_URL ||
  (typeof window !== 'undefined' &&
  window.location &&
  window.location.hostname &&
  window.location.hostname.includes('onrender.com')
    ? 'https://pillsync-care.onrender.com'
    : 'http://localhost:8000');
