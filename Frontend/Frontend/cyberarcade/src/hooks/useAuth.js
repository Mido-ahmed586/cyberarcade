// src/hooks/useAuth.js
//
// Authentication hook backed by the real /api/auth endpoints.
//
// Behavior:
//   - On first mount, if a JWT exists in localStorage, call /api/auth/me and
//     populate `user`. While that check is in flight, `authReady` is false so
//     App.jsx can show the boot screen instead of flashing the landing page.
//   - login(credentials) → calls authService.login, stores tokens, fetches /me,
//     returns the user. Throws on failure so the Auth page can show an error.
//   - register(...) → calls register + login.
//   - logout() → clears tokens and state.
//   - The api layer calls us via registerUnauthorizedHandler when a refresh
//     fails, so expired sessions drop back to an unauthenticated state cleanly.

import { useCallback, useEffect, useState } from "react";
import {
  getAccessToken,
  clearTokens,
  registerUnauthorizedHandler,
} from "../services/api";
import { authService } from "../services/auth.service";

export function useAuth() {
  const [user, setUser] = useState(null);
  const [authReady, setAuthReady] = useState(false);

  // Hydrate on mount: if we have a token, verify it by fetching /me.
  useEffect(() => {
    let cancelled = false;

    const hydrate = async () => {
      if (!getAccessToken()) {
        if (!cancelled) setAuthReady(true);
        return;
      }
      try {
        const me = await authService.me();
        if (!cancelled) setUser(me);
      } catch {
        clearTokens();
      } finally {
        if (!cancelled) setAuthReady(true);
      }
    };

    hydrate();
    return () => {
      cancelled = true;
    };
  }, []);

  // Let the api layer force-logout us on refresh failure.
  useEffect(() => {
    registerUnauthorizedHandler(() => setUser(null));
  }, []);

  const login = useCallback(async ({ email, password }) => {
    await authService.login({ email, password });
    const me = await authService.me();
    setUser(me);
    return me;
  }, []);

  const register = useCallback(async ({ name, email, password }) => {
    await authService.register({ name, email, password });
    // The register endpoint doesn't return a token, so log in immediately.
    await authService.login({ email, password });
    const me = await authService.me();
    setUser(me);
    return me;
  }, []);

  const logout = useCallback(() => {
    authService.logout();
    setUser(null);
  }, []);

  const googleAuth = useCallback(async (credential) => {
    await authService.googleAuth(credential);
    const me = await authService.me();
    setUser(me);
    return me;
  }, []);

  return { user, authReady, login, register, logout, googleAuth };
}
