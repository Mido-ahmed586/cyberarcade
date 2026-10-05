import { useState } from "react";
import Navbar from "../components/layout/Navbar";
import I from "../components/icons/Icons";
import { api } from "../services/api";

const TABS = [
  { id: "account",       label: "Account",       icon: <I.User /> },
  { id: "appearance",    label: "Appearance",     icon: <I.Monitor /> },
  { id: "privacy",       label: "Privacy",        icon: <I.Eye /> },
  { id: "notifications", label: "Notifications",  icon: <I.Mail /> },
  { id: "danger",        label: "Danger Zone",    icon: <I.X /> },
];

function Toggle({ checked, onChange }) {
  return (
    <button
      className={`stg-toggle${checked ? " stg-toggle-on" : ""}`}
      onClick={() => onChange(!checked)}
      role="switch"
      aria-checked={checked}
    >
      <span className="stg-toggle-knob" />
    </button>
  );
}

function SettingRow({ label, description, children }) {
  return (
    <div className="stg-row">
      <div className="stg-row-text">
        <div className="stg-row-label">{label}</div>
        {description && <div className="stg-row-desc">{description}</div>}
      </div>
      <div className="stg-row-ctrl">{children}</div>
    </div>
  );
}

function SectionCard({ title, children }) {
  return (
    <div className="stg-card">
      {title && <div className="stg-card-title">{title}</div>}
      {children}
    </div>
  );
}

// ── Account tab ────────────────────────────────────────────────────────────────
function AccountTab({ user, onLogout }) {
  const [pwForm, setPwForm] = useState({ current: "", next: "", confirm: "" });
  const [pwBusy, setPwBusy] = useState(false);
  const [pwMsg, setPwMsg]   = useState({ type: "", text: "" });

  const [nameForm, setNameForm] = useState({ name: user?.full_name || "" });
  const [nameBusy, setNameBusy] = useState(false);
  const [nameMsg, setNameMsg]   = useState({ type: "", text: "" });

  const handleChangeName = async (e) => {
    e.preventDefault();
    if (!nameForm.name.trim()) return;
    setNameBusy(true);
    setNameMsg({ type: "", text: "" });
    try {
      await api.patch("/api/auth/me", { full_name: nameForm.name.trim() });
      setNameMsg({ type: "ok", text: "Name updated successfully." });
    } catch (err) {
      setNameMsg({ type: "err", text: err?.message || "Failed to update name." });
    } finally { setNameBusy(false); }
  };

  const handleChangePw = async (e) => {
    e.preventDefault();
    if (!pwForm.current || !pwForm.next) { setPwMsg({ type: "err", text: "Fill in all fields." }); return; }
    if (pwForm.next !== pwForm.confirm) { setPwMsg({ type: "err", text: "New passwords do not match." }); return; }
    if (pwForm.next.length < 8) { setPwMsg({ type: "err", text: "Password must be at least 8 characters." }); return; }
    setPwBusy(true);
    setPwMsg({ type: "", text: "" });
    try {
      await api.post("/api/auth/change-password", { current_password: pwForm.current, new_password: pwForm.next });
      setPwMsg({ type: "ok", text: "Password changed successfully." });
      setPwForm({ current: "", next: "", confirm: "" });
    } catch (err) {
      setPwMsg({ type: "err", text: err?.message || "Incorrect current password." });
    } finally { setPwBusy(false); }
  };

  return (
    <div className="stg-tab-content">
      {/* Profile info */}
      <SectionCard title="Profile Information">
        <form className="stg-form" onSubmit={handleChangeName}>
          <div className="stg-field">
            <label>Full Name</label>
            <input
              value={nameForm.name}
              onChange={(e) => setNameForm({ name: e.target.value })}
              placeholder="Your full name"
            />
          </div>
          <div className="stg-field">
            <label>Email Address</label>
            <input value={user?.email || ""} readOnly className="stg-readonly" />
            <span className="stg-hint">Email address cannot be changed here.</span>
          </div>
          <div className="stg-field">
            <label>Role</label>
            <input value={user?.role || "student"} readOnly className="stg-readonly" style={{ textTransform: "capitalize" }} />
          </div>
          {nameMsg.text && <div className={`afb ${nameMsg.type === "ok" ? "ok" : "no"}`}>{nameMsg.text}</div>}
          <button className="btn ba2 bs stg-save" type="submit" disabled={nameBusy}>
            {nameBusy ? "Saving…" : "Save Changes"}
          </button>
        </form>
      </SectionCard>

      {/* Password change */}
      <SectionCard title="Change Password">
        <form className="stg-form" onSubmit={handleChangePw}>
          <div className="stg-field">
            <label>Current Password</label>
            <input
              type="password"
              value={pwForm.current}
              onChange={(e) => setPwForm((p) => ({ ...p, current: e.target.value }))}
              placeholder="Enter current password"
              autoComplete="current-password"
            />
          </div>
          <div className="stg-field">
            <label>New Password</label>
            <input
              type="password"
              value={pwForm.next}
              onChange={(e) => setPwForm((p) => ({ ...p, next: e.target.value }))}
              placeholder="At least 8 characters"
              autoComplete="new-password"
            />
          </div>
          <div className="stg-field">
            <label>Confirm New Password</label>
            <input
              type="password"
              value={pwForm.confirm}
              onChange={(e) => setPwForm((p) => ({ ...p, confirm: e.target.value }))}
              placeholder="Repeat new password"
              autoComplete="new-password"
            />
          </div>
          {pwMsg.text && <div className={`afb ${pwMsg.type === "ok" ? "ok" : "no"}`}>{pwMsg.text}</div>}
          <button className="btn ba2 bs stg-save" type="submit" disabled={pwBusy}>
            {pwBusy ? "Updating…" : "Update Password"}
          </button>
        </form>
      </SectionCard>
    </div>
  );
}

// ── Appearance tab ─────────────────────────────────────────────────────────────
function AppearanceTab({ theme, setTheme }) {
  return (
    <div className="stg-tab-content">
      <SectionCard title="Theme">
        <div className="stg-theme-grid">
          {[
            { key: "dark",  label: "Dark",  desc: "Dark background, easy on the eyes" },
            { key: "light", label: "Light", desc: "Light background, better in sunlight" },
          ].map((t) => (
            <button
              key={t.key}
              className={`stg-theme-opt${theme === t.key ? " stg-theme-active" : ""}`}
              onClick={() => setTheme(t.key)}
            >
              <div className={`stg-theme-preview stg-preview-${t.key}`}>
                <div className="stg-preview-bar" />
                <div className="stg-preview-line" />
                <div className="stg-preview-line stg-preview-line-sm" />
              </div>
              <div className="stg-theme-label">{t.label}</div>
              <div className="stg-theme-desc">{t.desc}</div>
              {theme === t.key && <div className="stg-theme-check"><I.Check /></div>}
            </button>
          ))}
        </div>
      </SectionCard>

      <SectionCard title="Display">
        <SettingRow label="Compact Mode" description="Reduce spacing between elements for denser layouts">
          <Toggle checked={false} onChange={() => {}} />
        </SettingRow>
        <SettingRow label="Reduce Animations" description="Minimize motion effects throughout the app">
          <Toggle checked={false} onChange={() => {}} />
        </SettingRow>
      </SectionCard>
    </div>
  );
}

// ── Privacy tab ────────────────────────────────────────────────────────────────
function PrivacyTab() {
  const [leaderboard, setLeaderboard] = useState(true);
  const [publicProfile, setPublicProfile] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState({ type: "", text: "" });

  const handleSave = async () => {
    setSaving(true);
    setMsg({ type: "", text: "" });
    try {
      await api.patch("/api/auth/me/privacy", { leaderboard_visible: leaderboard, public_profile: publicProfile });
      setMsg({ type: "ok", text: "Privacy settings saved." });
    } catch {
      setMsg({ type: "err", text: "Failed to save — try again later." });
    } finally { setSaving(false); }
  };

  return (
    <div className="stg-tab-content">
      <SectionCard title="Visibility">
        <SettingRow label="Appear on Leaderboard" description="Allow your username and XP to appear on the public leaderboard">
          <Toggle checked={leaderboard} onChange={setLeaderboard} />
        </SettingRow>
        <SettingRow label="Public Profile" description="Let other students view your profile and badge collection">
          <Toggle checked={publicProfile} onChange={setPublicProfile} />
        </SettingRow>
      </SectionCard>

      {msg.text && <div className={`afb ${msg.type === "ok" ? "ok" : "no"}`} style={{ marginTop: 16 }}>{msg.text}</div>}
      <button className="btn ba2 bs stg-save" onClick={handleSave} disabled={saving}>
        {saving ? "Saving…" : "Save Privacy Settings"}
      </button>
    </div>
  );
}

// ── Notifications tab ──────────────────────────────────────────────────────────
function NotificationsTab() {
  const [prefs, setPrefs] = useState({
    badge_earned: true,
    streak_reminder: true,
    new_course: false,
    weekly_digest: true,
  });
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState({ type: "", text: "" });

  const toggle = (key) => setPrefs((p) => ({ ...p, [key]: !p[key] }));

  const handleSave = async () => {
    setSaving(true);
    setMsg({ type: "", text: "" });
    try {
      await api.patch("/api/auth/me/notifications", prefs);
      setMsg({ type: "ok", text: "Notification preferences saved." });
    } catch {
      setMsg({ type: "err", text: "Failed to save — try again later." });
    } finally { setSaving(false); }
  };

  return (
    <div className="stg-tab-content">
      <SectionCard title="Email Notifications">
        <SettingRow label="Badge Earned" description="Get an email when you unlock a new badge">
          <Toggle checked={prefs.badge_earned} onChange={() => toggle("badge_earned")} />
        </SettingRow>
        <SettingRow label="Streak Reminders" description="Daily reminder to maintain your login streak">
          <Toggle checked={prefs.streak_reminder} onChange={() => toggle("streak_reminder")} />
        </SettingRow>
        <SettingRow label="New Course Available" description="Notify me when new courses or labs are published">
          <Toggle checked={prefs.new_course} onChange={() => toggle("new_course")} />
        </SettingRow>
        <SettingRow label="Weekly Digest" description="A weekly summary of your progress and platform highlights">
          <Toggle checked={prefs.weekly_digest} onChange={() => toggle("weekly_digest")} />
        </SettingRow>
      </SectionCard>

      {msg.text && <div className={`afb ${msg.type === "ok" ? "ok" : "no"}`} style={{ marginTop: 16 }}>{msg.text}</div>}
      <button className="btn ba2 bs stg-save" onClick={handleSave} disabled={saving}>
        {saving ? "Saving…" : "Save Preferences"}
      </button>
    </div>
  );
}

// ── Danger Zone tab ────────────────────────────────────────────────────────────
function DangerTab({ onLogout }) {
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy]       = useState(false);
  const [msg, setMsg]         = useState({ type: "", text: "" });

  const handleDelete = async () => {
    if (confirm !== "DELETE") { setMsg({ type: "err", text: 'Type DELETE (all caps) to confirm.' }); return; }
    setBusy(true);
    setMsg({ type: "", text: "" });
    try {
      await api.delete("/api/auth/me");
      onLogout();
    } catch (err) {
      setMsg({ type: "err", text: err?.message || "Failed to delete account." });
      setBusy(false);
    }
  };

  return (
    <div className="stg-tab-content">
      <SectionCard>
        <div className="stg-danger-header">
          <div className="stg-danger-icon"><I.X /></div>
          <div>
            <div className="stg-danger-title">Delete Account</div>
            <div className="stg-danger-desc">
              Permanently delete your account and all associated data including progress, badges, certificates, and XP. This action cannot be undone.
            </div>
          </div>
        </div>
        <div className="stg-danger-confirm">
          <label>Type <strong>DELETE</strong> to confirm</label>
          <input
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            placeholder="DELETE"
            className="stg-danger-input"
          />
          {msg.text && <div className={`afb ${msg.type === "ok" ? "ok" : "no"}`}>{msg.text}</div>}
          <button
            className="btn stg-delete-btn"
            onClick={handleDelete}
            disabled={busy}
          >
            {busy ? "Deleting…" : "Delete My Account"}
          </button>
        </div>
      </SectionCard>

      <SectionCard title="Session">
        <SettingRow label="Sign out of all devices" description="Revokes all active sessions including this one">
          <button className="btn bg bs" onClick={onLogout}>Sign Out</button>
        </SettingRow>
      </SectionCard>
    </div>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────────
export default function Settings({ theme, setTheme, user, nav, onLogout, currentPage, currentStreak }) {
  const [activeTab, setActiveTab] = useState("account");

  const renderTab = () => {
    switch (activeTab) {
      case "account":       return <AccountTab user={user} onLogout={onLogout} />;
      case "appearance":    return <AppearanceTab theme={theme} setTheme={setTheme} />;
      case "privacy":       return <PrivacyTab />;
      case "notifications": return <NotificationsTab />;
      case "danger":        return <DangerTab onLogout={onLogout} />;
      default:              return null;
    }
  };

  return (
    <div className="pg">
      <Navbar theme={theme} setTheme={setTheme} user={user} nav={nav} onLogout={onLogout} currentPage={currentPage} currentStreak={currentStreak} />
      <div className="stg-page">
        <div className="stg-header">
          <button className="bkb" onClick={() => nav("dashboard")}>← Back</button>
          <h1>Settings</h1>
          <p>Manage your account, appearance, and privacy preferences.</p>
        </div>

        <div className="stg-layout">
          {/* Sidebar tabs */}
          <nav className="stg-nav">
            {TABS.map((t) => (
              <button
                key={t.id}
                className={`stg-nav-item${activeTab === t.id ? " stg-nav-active" : ""}${t.id === "danger" ? " stg-nav-danger" : ""}`}
                onClick={() => setActiveTab(t.id)}
              >
                <span className="stg-nav-icon">{t.icon}</span>
                {t.label}
              </button>
            ))}
          </nav>

          {/* Tab content */}
          <div className="stg-main">
            {renderTab()}
          </div>
        </div>
      </div>
    </div>
  );
}
