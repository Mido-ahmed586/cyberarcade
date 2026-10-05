import { useState, useEffect } from "react";
import Navbar from "../components/layout/Navbar";
import { InlineLoader } from "../components/ui/Loader";
import I from "../components/icons/Icons";

export default function Auth({
  mode,
  theme,
  setTheme,
  onLogin,
  onRegister,
  onGoogleAuth,
  nav,
  user,
  onLogout,
  currentPage,
}) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  // Load Google Sign-In script
  useEffect(() => {
    const existingScript = document.getElementById("google-gsi");
    if (existingScript) return;

    const script = document.createElement("script");
    script.id = "google-gsi";
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);

    return () => {};
  }, []);

  // Initialize Google button when script loads and mode changes
  useEffect(() => {
    const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    if (!googleClientId) return;

    const initGoogle = () => {
      if (!window.google?.accounts?.id) return;

      window.google.accounts.id.initialize({
        client_id: googleClientId,
        callback: handleGoogleResponse,
      });

      const container = document.getElementById("google-btn");
      if (container) {
        container.innerHTML = "";
        window.google.accounts.id.renderButton(container, {
          theme: theme === "dark" ? "filled_black" : "outline",
          size: "large",
          width: "100%",
          text: mode === "login" ? "signin_with" : "signup_with",
          shape: "pill",
        });
      }
    };

    // Script may already be loaded or still loading
    if (window.google?.accounts?.id) {
      initGoogle();
    } else {
      const interval = setInterval(() => {
        if (window.google?.accounts?.id) {
          clearInterval(interval);
          initGoogle();
        }
      }, 200);
      const timeout = setTimeout(() => clearInterval(interval), 5000);
      return () => { clearInterval(interval); clearTimeout(timeout); };
    }
  }, [mode, theme]);

  const handleGoogleResponse = async (response) => {
    if (!response.credential) return;
    setBusy(true);
    setError("");
    try {
      await onGoogleAuth(response.credential);
    } catch (e) {
      setError(e.message || "Google sign-in failed");
    } finally {
      setBusy(false);
    }
  };

  const submit = async () => {
    setError("");

    if (mode === "register" && (!name || name.trim().length < 2)) {
      setError("Name must be at least 2 characters");
      return;
    }
    if (!email || !password) {
      setError("All fields required");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    setBusy(true);
    try {
      if (mode === "register") {
        await onRegister({ name: name.trim(), email: email.trim(), password });
      } else {
        await onLogin({ email: email.trim(), password });
      }
    } catch (e) {
      setError(e.message || "Something went wrong");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="pg ap">
      <Navbar
        theme={theme}
        setTheme={setTheme}
        nav={nav}
        user={user}
        onLogout={onLogout}
        currentPage={currentPage}
      />
      <div className="aw">
        <div className="ab2">
          <div className="at">
            <div className="bm sm">
              <svg
                width="22"
                height="22"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              </svg>
            </div>
            <h2>{mode === "login" ? "Welcome Back" : "Join CyberArcade"}</h2>
            <p>
              {mode === "login"
                ? "Access your training dashboard"
                : "Begin your cybersecurity journey"}
            </p>
          </div>

          {error && <div className="ae">{error}</div>}

          {/* Google Sign-In Button */}
          <div id="google-btn" className="google-btn-wrap"></div>

          {import.meta.env.VITE_GOOGLE_CLIENT_ID && (
            <div className="auth-divider">
              <span>or</span>
            </div>
          )}

          {mode === "register" && (
            <div className="fg3">
              <label>Full Name</label>
              <input
                placeholder="Agent Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={busy}
              />
            </div>
          )}

          <div className="fg3">
            <label>Email</label>
            <input
              type="email"
              placeholder="agent@cyberarcade.io"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={busy}
            />
          </div>

          <div className="fg3">
            <label>Password</label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !busy && submit()}
              disabled={busy}
            />
          </div>

          <button className="btn ba2 bf" onClick={submit} disabled={busy}>
            {busy ? (
              <InlineLoader />
            ) : mode === "login" ? (
              "Sign In"
            ) : (
              "Create Account"
            )}
          </button>

          <p className="asw">
            {mode === "login" ? "New here? " : "Have an account? "}
            <button
              onClick={() => nav(mode === "login" ? "register" : "login")}
              disabled={busy}
            >
              {mode === "login" ? "Create account" : "Sign in"}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
