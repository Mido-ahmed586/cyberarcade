// src/services/api.js
//
// Central axios client for the CyberArcade backend.
//
// - Reads base URL from VITE_API_URL (see .env / .env.example).
// - Attaches the JWT access token from localStorage to every request.
// - On 401 responses, tries exactly once to refresh the access token with the
//   refresh token. If the refresh succeeds, the original request is retried.
//   If it fails, tokens are cleared and the user is sent back to login.
// - Exposes a tiny `api` helper with .get/.post/.put/.delete that returns
//   response.data (not the full axios envelope) so call sites stay clean.

import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export const TOKEN_KEY = "cyberarcade.access_token";
export const REFRESH_KEY = "cyberarcade.refresh_token";

export function getAccessToken() {
  return localStorage.getItem(TOKEN_KEY);
}
export function getRefreshToken() {
  return localStorage.getItem(REFRESH_KEY);
}
export function setTokens({ access_token, refresh_token }) {
  if (access_token) localStorage.setItem(TOKEN_KEY, access_token);
  if (refresh_token) localStorage.setItem(REFRESH_KEY, refresh_token);
}
export function clearTokens() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

// Callback the AuthProvider registers so we can force a logout from here
// when refresh fails. Keeps api.js free of React imports.
let onUnauthorized = null;
export function registerUnauthorizedHandler(fn) {
  onUnauthorized = fn;
}

const http = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// --- Request interceptor: attach JWT -----------------------------------------
http.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// --- Response interceptor: refresh on 401 ------------------------------------
let refreshInFlight = null;

async function refreshAccessToken() {
  const refresh = getRefreshToken();
  if (!refresh) throw new Error("No refresh token");

  // Use a bare axios call so we don't recurse through our own interceptors.
  const res = await axios.post(
    `${BASE_URL}/api/auth/refresh`,
    { refresh_token: refresh },
    { headers: { "Content-Type": "application/json" } }
  );
  setTokens(res.data);
  return res.data.access_token;
}

http.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config || {};
    const status = error.response?.status;

    // Don't try to refresh the refresh endpoint itself, or retry twice.
    const isAuthEndpoint =
      original.url?.includes("/api/auth/login") ||
      original.url?.includes("/api/auth/register") ||
      original.url?.includes("/api/auth/refresh");

    if (status === 401 && !original._retried && !isAuthEndpoint) {
      original._retried = true;
      try {
        refreshInFlight = refreshInFlight || refreshAccessToken();
        const newToken = await refreshInFlight;
        refreshInFlight = null;
        original.headers = original.headers || {};
        original.headers.Authorization = `Bearer ${newToken}`;
        return http(original);
      } catch (e) {
        refreshInFlight = null;
        clearTokens();
        if (onUnauthorized) onUnauthorized();
        return Promise.reject(e);
      }
    }

    return Promise.reject(error);
  }
);

// --- Public helper: normalized error messages + .data unwrapping -------------
function unwrap(promise) {
  return promise
    .then((res) => res.data)
    .catch((err) => {
      // FastAPI returns { detail: "..." } or { detail: [{ msg, loc, ... }] }
      const detail = err?.response?.data?.detail;
      let message;
      if (Array.isArray(detail)) {
        message = detail.map((d) => d.msg || JSON.stringify(d)).join("; ");
      } else if (typeof detail === "string") {
        message = detail;
      } else {
        if (!err.response && err.message?.includes("Network")) {
        message = "Network Error";
      } else {
        message = err.message || "Request failed";
      }
      }
      const wrapped = new Error(message);
      wrapped.status = err?.response?.status;
      wrapped.original = err;
      throw wrapped;
    });
}

export const api = {
  get: (path, config) => unwrap(http.get(path, config)),
  post: (path, body, config) => unwrap(http.post(path, body, config)),
  put: (path, body, config) => unwrap(http.put(path, body, config)),
  patch: (path, body, config) => unwrap(http.patch(path, body, config)),
  delete: (path, config) => unwrap(http.delete(path, config)),
  raw: http, // escape hatch if a caller ever needs headers/status
};

export { BASE_URL };