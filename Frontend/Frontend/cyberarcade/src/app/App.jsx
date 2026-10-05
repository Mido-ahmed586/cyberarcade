import { useState, useEffect, useRef } from "react";
import { useTheme } from "../hooks/useTheme";
import { useAuth } from "../hooks/useAuth";
import { CyberLoader } from "../components/ui/Loader";
import Chat from "../components/layout/Chat";
import I from "../components/icons/Icons";
import { subscriptionService } from "../services/subscription.service";
import { authService } from "../services/auth.service";
import { gamificationService } from "../services/gamification.service";
import { getAccessToken } from "../services/api";
import Landing from "../pages/Landing";
import Auth from "../pages/Auth";
import Dashboard from "../pages/Dashboard";
import Courses from "../pages/Courses";
import CourseDetail from "../pages/CourseDetail";
import Lab from "../pages/Lab";
import AdminPanel from "../pages/AdminPanel";
import InstructorPanel from "../pages/InstructorPanel";
import Profile from "../pages/Profile";
import Subscription from "../pages/Subscription";
import Certificates from "../pages/Certificates";
import AICoach from "../pages/AICoach";
import Leaderboard from "../pages/Leaderboard";
import Badges from "../pages/Badges";
import Settings from "../pages/Settings";
import "../styles/global.css";

const BOOT_MESSAGES = [
  "Initializing secure tunnel...",
  "Loading attack modules...",
  "Deploying sandbox...",
  "System ready.",
];

const PROTECTED_PAGES = [
  "dashboard","courses","course-detail","lab",
  "admin","instructor","profile","subscription","certificates","ai-coach","leaderboard","badges","settings",
];

// ── Session storage helpers ────────────────────────────────────────────────
// We persist { page, course, lab } so a full refresh keeps the user exactly
// where they were, and browser history entries carry the same state so
// back/forward work correctly.

const SS_KEY = "ca_nav";

function saveSession(page, course, lab) {
  try {
    sessionStorage.setItem(SS_KEY, JSON.stringify({ page, course, lab }));
  } catch { /* quota / private mode */ }
}

function loadSession() {
  try {
    const raw = sessionStorage.getItem(SS_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

function clearSession() {
  try { sessionStorage.removeItem(SS_KEY); } catch { /* ignore */ }
}

export default function App() {
  const { theme, setTheme } = useTheme();
  const { user, authReady, login, register, logout, googleAuth } = useAuth();

  // Restore whatever was saved before the refresh (or fall back to landing)
  const restored = useRef(loadSession());

  const [page, setPage]                   = useState(restored.current?.page || "landing");
  const [selectedCourse, setSelectedCourse] = useState(restored.current?.course || null);
  const [selectedLab, setSelectedLab]     = useState(restored.current?.lab    || null);

  const [loading, setLoading]   = useState(true);
  const [loadText, setLoadText] = useState(BOOT_MESSAGES[0]);
  const [chatOpen, setChatOpen] = useState(false);
  const [userPlan, setUserPlan] = useState("free");
  const [currentStreak, setCurrentStreak] = useState(0);
  const [verifyMsg, setVerifyMsg] = useState("");
  const [resendBusy, setResendBusy] = useState(false);

  // Keep sessionStorage in sync whenever page/course/lab changes
  useEffect(() => {
    saveSession(page, selectedCourse, selectedLab);
  }, [page, selectedCourse, selectedLab]);

  // Boot sequence
  useEffect(() => {
    let i = 0;
    const iv = setInterval(() => {
      i++;
      if (i < BOOT_MESSAGES.length) setLoadText(BOOT_MESSAGES[i]);
      else clearInterval(iv);
    }, 700);
    return () => clearInterval(iv);
  }, []);

  // Wait for auth to resolve
  useEffect(() => {
    if (!authReady) return;
    const t = setTimeout(() => setLoading(false), 500);
    return () => clearTimeout(t);
  }, [authReady]);

  // Auth-based redirects (only when auth first resolves, not on every render)
  useEffect(() => {
    if (!authReady) return;

    if (user) {
      // Logged-in: if somehow stuck on landing, go to dashboard
      if (page === "landing" || page === "login" || page === "register") {
        goTo("dashboard");
      }
    } else {
      // Logged-out: kick off any protected page
      if (PROTECTED_PAGES.includes(page)) {
        clearSession();
        goTo("landing");
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, authReady]);

  // Load subscription plan
  useEffect(() => {
    if (!user) { setUserPlan("free"); return; }
    subscriptionService.getUserPlan().then(setUserPlan);
  }, [user]);

  // Load current streak for navbar chip
  useEffect(() => {
    if (!user) { setCurrentStreak(0); return; }
    gamificationService.dashboard()
      .then((d) => setCurrentStreak(d?.streak?.current_streak || 0))
      .catch(() => {});
  }, [user]);

  // Handle email verification + payment redirect params
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const verifyToken  = params.get("verify");
    const paymentStatus = params.get("payment");

    if (verifyToken) {
      window.history.replaceState({}, "", window.location.pathname + window.location.hash);
      authService.verifyEmail(verifyToken)
        .then(() => setVerifyMsg("Email verified successfully! You can now sign in."))
        .catch(() => setVerifyMsg("Verification link is invalid or expired."));
    }

    if (paymentStatus) {
      window.history.replaceState({}, "", window.location.pathname + window.location.hash);
      if (paymentStatus === "success") {
        setVerifyMsg("Payment successful — your premium plan is now active.");
        subscriptionService.getUserPlan().then(setUserPlan).catch(() => {});
      } else if (paymentStatus === "cancelled") {
        setVerifyMsg("Payment cancelled — you have not been charged.");
      }
    }
  }, []);

  // ── Browser back / forward ─────────────────────────────────────────────
  useEffect(() => {
    const onPopState = (e) => {
      const state = e.state;
      if (!state?.page) return;

      // Guard: protected pages need a logged-in user
      if (!user && PROTECTED_PAGES.includes(state.page)) {
        goTo("landing");
        return;
      }
      // Role guards
      if (state.page === "admin" && !["admin","system_admin"].includes(user?.role)) return;
      if (state.page === "instructor" && !["instructor","admin","system_admin"].includes(user?.role)) return;

      // Restore associated data if the history entry carries it
      if (state.course) setSelectedCourse(state.course);
      if (state.lab)    setSelectedLab(state.lab);

      // Update session so a subsequent refresh lands here too
      saveSession(state.page, state.course || selectedCourse, state.lab || selectedLab);
      setPage(state.page);
    };

    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, selectedCourse, selectedLab]);

  // ── Seed the very first history entry so "back" never leaves the app ──
  useEffect(() => {
    // Replace the initial entry (which has no state) with the current page
    window.history.replaceState(
      { page, course: selectedCourse, lab: selectedLab },
      "",
      window.location.href
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // runs once on mount

  // ── Core navigation ───────────────────────────────────────────────────
  // Internal helper — sets page state without pushing history (used for
  // auth redirects so we don't pollute the history stack).
  const goTo = (p, course, lab) => {
    if (course) setSelectedCourse(course);
    if (lab)    setSelectedLab(lab);
    setPage(p);
  };

  // Public nav() — called by every button/link in the app.
  const nav = (p, data) => {
    if (p === "admin"      && !["admin","system_admin"].includes(user?.role)) return;
    if (p === "instructor" && !["instructor","admin","system_admin"].includes(user?.role)) return;

    // Guard: if navigating to a protected page without a valid token, go to login
    if (PROTECTED_PAGES.includes(p) && !getAccessToken()) {
      clearSession();
      setPage("login");
      return;
    }

    const course = data?.course ?? selectedCourse;
    const lab    = data?.lab    ?? selectedLab;

    // Persist atomically NOW so F5 during the loading animation restores the right page+lab
    saveSession(p, course, lab);

    if (data?.course) setSelectedCourse(data.course);
    if (data?.lab)    setSelectedLab(data.lab);

    // Push a real history entry so back/forward work
    window.history.pushState(
      { page: p, course: data?.course || null, lab: data?.lab || null },
      "",
      window.location.pathname + window.location.search
    );

    setLoading(true);
    setLoadText("Loading...");
    setTimeout(() => { setPage(p); setLoading(false); }, 400);
  };

  // ── Auth handlers ─────────────────────────────────────────────────────
  const handleLogin = async ({ email, password }) => {
    await login({ email, password });
    nav("dashboard");
  };

  const handleRegister = async ({ name, email, password }) => {
    await register({ name, email, password });
    try { await authService.notifyAdminNewUser({ name, email }); } catch { /* non-fatal */ }
    nav("dashboard");
  };

  const handleGoogleAuth = async (credential) => {
    await googleAuth(credential);
    nav("dashboard");
  };

  const handleResendVerification = async () => {
    if (!user?.email || resendBusy) return;
    setResendBusy(true);
    try {
      await authService.resendVerification(user.email);
      setVerifyMsg("Verification email sent! Check your inbox.");
    } catch { setVerifyMsg("Failed to resend. Try again later."); }
    finally { setResendBusy(false); }
  };

  const handleLogout = () => {
    logout();
    setUserPlan("free");
    clearSession();
    // Clear history state on logout
    window.history.replaceState({ page: "landing" }, "", window.location.pathname);
    setPage("landing");
  };

  // ── Render ─────────────────────────────────────────────────────────────
  if (loading || !authReady) {
    return (
      <div className="app">
        <div className="ls"><CyberLoader text={loadText} /></div>
      </div>
    );
  }

  const showFab = user && !["landing","login","register","lab","admin","instructor"].includes(page);
  const shared  = {
    theme, setTheme, user, nav, onLogout: handleLogout, currentPage: page, userPlan,
    onGamiRewards: () => {
      gamificationService.dashboard()
        .then((d) => setCurrentStreak(d?.streak?.current_streak || 0))
        .catch(() => {});
    },
    currentStreak,
  };

  return (
    <div className="app">
      {page === "landing"  && <Landing  {...shared} />}
      {page === "login"    && <Auth mode="login"    {...shared} onLogin={handleLogin} onRegister={handleRegister} onGoogleAuth={handleGoogleAuth} />}
      {page === "register" && <Auth mode="register" {...shared} onLogin={handleLogin} onRegister={handleRegister} onGoogleAuth={handleGoogleAuth} />}

      {verifyMsg && (
        <div className="verify-banner">
          <span>{verifyMsg}</span>
          <button className="ib" onClick={() => setVerifyMsg("")}><I.X /></button>
        </div>
      )}

      {user && !user.email_verified && !["login","register","landing"].includes(page) && (
        <div className="verify-warn">
          <I.Mail />
          <span>Please verify your email address to unlock all features.</span>
          <button className="btn ba2 bs" onClick={handleResendVerification} disabled={resendBusy}>
            {resendBusy ? "Sending..." : "Resend Email"}
          </button>
        </div>
      )}

      {page === "dashboard"    && <Dashboard    {...shared} />}
      {page === "courses"      && <Courses      {...shared} />}
      {page === "course-detail" && <CourseDetail {...shared} course={selectedCourse} />}
      {page === "lab"          && <Lab          {...shared} lab={selectedLab} chatOpen={chatOpen} setChatOpen={setChatOpen} />}
      {page === "admin"        && <AdminPanel   {...shared} />}
      {page === "instructor"   && <InstructorPanel {...shared} />}
      {page === "profile"      && <Profile      {...shared} />}
      {page === "subscription"  && <Subscription  {...shared} onPlanChange={setUserPlan} />}
      {page === "certificates"  && <Certificates  {...shared} />}
      {page === "ai-coach"      && <AICoach      {...shared} />}
      {page === "leaderboard"   && <Leaderboard  {...shared} />}
      {page === "badges"        && <Badges       {...shared} />}
      {page === "settings"      && <Settings     {...shared} />}

      {showFab && (
        <button className="fab" onClick={() => setChatOpen(!chatOpen)}>
          {chatOpen ? <I.X /> : <I.Bot />}
        </button>
      )}

      {chatOpen && page !== "lab" && (
        <Chat onClose={() => setChatOpen(false)} />
      )}
    </div>
  );
}
