import { useEffect, useState } from "react";
import Navbar from "../components/layout/Navbar";
import I from "../components/icons/Icons";
import { certificatesService } from "../services/certificates.service";
import { InlineLoader } from "../components/ui/Loader";

function fmtDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-US", {
    year: "numeric", month: "long", day: "numeric",
  });
}

function copyToClipboard(text) {
  navigator.clipboard?.writeText(text).catch(() => {});
}

// ── Certificate card ──────────────────────────────────────────────────────────
function CertCard({ cert, onDownload, downloading, onView, viewing }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    copyToClipboard(cert.serial_number);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };

  return (
    <div className="cert-card">
      <div className="cert-card-glow" />
      <div className="cert-card-body">
        <div className="cert-badge"><I.Shield /></div>
        <div className="cert-info">
          <div className="cert-status-row">
            <span className="cert-status-dot" />
            <span className="cert-status-label">Verified Certificate</span>
          </div>
          <h3 className="cert-course">{cert.course_name}</h3>
          <div className="cert-meta">
            <span><I.User /> {cert.student_name}</span>
            <span><I.Calendar /> {fmtDate(cert.issued_at)}</span>
          </div>
          <div className="cert-serial-row">
            <code className="cert-serial">{cert.serial_number}</code>
            <button className="cert-copy-btn" onClick={handleCopy} title="Copy serial number">
              {copied ? <I.Check /> : <I.Copy />}
            </button>
          </div>
        </div>
      </div>
      <div className="cert-card-footer">
        <div style={{ display: "flex", gap: 8 }}>
          <button
            className="btn bg bs cert-dl-btn"
            onClick={() => onView(cert)}
            disabled={viewing === cert.certificate_id}
          >
            {viewing === cert.certificate_id ? <span className="cert-spinner" /> : <I.Eye />}
            {viewing === cert.certificate_id ? "Opening…" : "View"}
          </button>
          <button
            className="btn ba2 bs cert-dl-btn"
            onClick={() => onDownload(cert)}
            disabled={downloading === cert.certificate_id}
          >
            {downloading === cert.certificate_id ? <span className="cert-spinner" /> : <I.Download />}
            {downloading === cert.certificate_id ? "…" : "Download"}
          </button>
        </div>
        <span className={`cert-validity ${cert.verification_status === "valid" ? "valid" : "revoked"}`}>
          {cert.verification_status === "valid" ? "● Active" : "✕ Revoked"}
        </span>
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function Certificates({ theme, setTheme, user, nav, onLogout, currentPage, userPlan }) {
  const [certs, setCerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [downloading, setDownloading] = useState(null);
  const [viewing, setViewing] = useState(null);

  useEffect(() => {
    certificatesService.myCertificates()
      .then(setCerts)
      .catch((e) => setError(e.message || "Failed to load certificates."))
      .finally(() => setLoading(false));
  }, []);

  const handleDownload = async (cert) => {
    setDownloading(cert.certificate_id);
    try {
      await certificatesService.download(cert.certificate_id, cert.serial_number);
    } catch { /* non-fatal */ }
    finally { setDownloading(null); }
  };

  const handleView = async (cert) => {
    setViewing(cert.certificate_id);
    try {
      await certificatesService.view(cert.certificate_id);
    } catch { /* non-fatal */ }
    finally { setViewing(null); }
  };

  return (
    <div className="app">
      <Navbar
        theme={theme} setTheme={setTheme}
        user={user} nav={nav} onLogout={onLogout}
        currentPage={currentPage} userPlan={userPlan}
      />

      <div className="cert-page">
        <div className="cert-page-header">
          <div className="cert-page-title">
            <div className="cert-title-icon"><I.Award /></div>
            <div>
              <h1>My Certificates</h1>
              <p>Proof of your cybersecurity achievements</p>
            </div>
          </div>
          <button className="btn bg bs" onClick={() => nav("profile")}>
            <I.User /> Back to Profile
          </button>
        </div>

        <div className="cert-list-full">
          {loading && <div style={{ padding: "40px 0" }}><InlineLoader /></div>}

          {!loading && error && (
            <div className="cert-error"><I.AlertTriangle /> {error}</div>
          )}

          {!loading && !error && certs.length === 0 && (
            <div className="cert-empty">
              <div className="cert-empty-icon"><I.Award /></div>
              <h3>No certificates yet</h3>
              <p>Complete all tasks in a course to earn your certificate.</p>
              <button className="btn ba2 bl" onClick={() => nav("courses")}>
                <I.Layers /> Start Learning
              </button>
            </div>
          )}

          <div className="cert-cards-grid">
            {!loading && certs.map((cert) => (
              <CertCard
                key={cert.certificate_id}
                cert={cert}
                onDownload={handleDownload}
                downloading={downloading}
                onView={handleView}
                viewing={viewing}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
