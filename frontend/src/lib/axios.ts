import axios from "axios";

// Single source of truth for the backend API base URL.
// - VITE_API_URL (build-time) is used when set (local .env and Vercel env).
// - Production builds must never fall back to localhost: a stale/missing env
//   var would silently send user requests to the visitor's own machine.
// - Local development keeps the localhost:8000 default.
export const API_BASE =
  import.meta.env.VITE_API_URL ||
  (import.meta.env.PROD ? `${window.location.origin}/api/v1` : "http://localhost:8000/api/v1");

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
