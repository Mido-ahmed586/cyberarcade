// src/services/auth.service.js

import { api, setTokens, clearTokens } from "./api";

export const authService = {
  register: ({ name, email, password }) =>
    api.post("/api/auth/register", {
      full_name: name,
      email,
      password,
    }),

  login: async ({ email, password }) => {
    const tokens = await api.post("/api/auth/login", { email, password });
    setTokens(tokens);
    return tokens;
  },

  googleAuth: async (credential) => {
    const tokens = await api.post("/api/auth/google", { credential });
    setTokens(tokens);
    return tokens;
  },

  verifyEmail: (token) =>
    api.post("/api/auth/verify-email", { token }),

  resendVerification: (email) =>
    api.post("/api/auth/resend-verification", { email }),

  me: () => api.get("/api/auth/me"),

  logout: () => {
    clearTokens();
    return Promise.resolve();
  },

  /**
   * Notify admins of a new user registration.
   * Hits /api/auth/notify-admin-new-user (non-blocking, fails silently).
   */
  notifyAdminNewUser: ({ name, email }) =>
    api.post("/api/auth/notify-admin-new-user", { full_name: name, email }).catch(() => {}),
};