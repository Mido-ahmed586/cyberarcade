import { useEffect, useState } from "react";
import Navbar from "../components/layout/Navbar";
import I from "../components/icons/Icons";
import { classesService } from "../services/classes.service";
import { coursesService } from "../services/courses.service";
import { certificatesService } from "../services/certificates.service";
import { subscriptionService } from "../services/subscription.service";
import { capitalize } from "../utils/helpers";
import { InlineLoader } from "../components/ui/Loader";

function fmtDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

// ── Compact certificate row used in profile ───────────────────────────────────
function ProfileCertCard({ cert, onDownload, downloading, onView, viewing }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard?.writeText(cert.serial_number).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  };

  return (
    <div className="prof-cert-card">
      <div className="prof-cert-left">
        <div className="prof-cert-icon"><I.Award /></div>
        <div className="prof-cert-info">
          <div className="prof-cert-course">{cert.course_name}</div>
          <div className="prof-cert-meta">
            <span><I.Calendar /> {fmtDate(cert.issued_at)}</span>
          </div>
          <div className="prof-cert-serial-row">
            <code className="prof-cert-serial">{cert.serial_number}</code>
            <button className="cert-copy-btn" onClick={handleCopy} title="Copy serial">
              {copied ? <I.Check /> : <I.Copy />}
            </button>
          </div>
        </div>
      </div>
      <div style={{ display: "flex", gap: 6 }}>
        <button
          className="btn bg bs prof-cert-dl"
          onClick={() => onView(cert)}
          disabled={viewing === cert.certificate_id}
          title="View in browser"
        >
          {viewing === cert.certificate_id ? <span className="cert-spinner" /> : <I.Eye />}
          {viewing === cert.certificate_id ? "…" : "View"}
        </button>
        <button
          className="btn ba2 bs prof-cert-dl"
          onClick={() => onDownload(cert)}
          disabled={downloading === cert.certificate_id}
          title="Download PDF"
        >
          {downloading === cert.certificate_id ? <span className="cert-spinner" /> : <I.Download />}
          {downloading === cert.certificate_id ? "…" : "PDF"}
        </button>
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function Profile({ theme, setTheme, user, nav, onLogout, currentPage, userPlan, currentStreak }) {
  const [enrolledClasses, setEnrolledClasses] = useState([]);
  const [classesLoading, setClassesLoading]   = useState(true);
  const [joinCode, setJoinCode]               = useState("");
  const [joinBusy, setJoinBusy]               = useState(false);
  const [joinMsg, setJoinMsg]                 = useState({ type: "", text: "" });

  const [certs, setCerts]           = useState([]);
  const [certsLoading, setCertsLoading] = useState(true);
  const [downloading, setDownloading]   = useState(null);
  const [viewing, setViewing]           = useState(null);

  const initials = (user?.full_name || "U").split(" ").map((w) => w[0]).join("").toUpperCase().slice(0, 2);

  useEffect(() => {
    classesService.enrolled()
      .then(setEnrolledClasses).catch(() => {})
      .finally(() => setClassesLoading(false));
    certificatesService.myCertificates()
      .then(setCerts).catch(() => {})
      .finally(() => setCertsLoading(false));
  }, []);

  const joinClass = async () => {
    if (!joinCode.trim()) return;
    setJoinBusy(true);
    setJoinMsg({ type: "", text: "" });
    try {
      await classesService.join(joinCode.trim());
      setJoinMsg({ type: "ok", text: "Successfully joined the class!" });
      setJoinCode("");
      const updated = await classesService.enrolled().catch(() => []);
      setEnrolledClasses(updated || []);
    } catch (e) {
      setJoinMsg({ type: "err", text: e.message || "Failed to join class" });
    } finally { setJoinBusy(false); }
  };

  const openClassCourse = async (cls) => {
    try {
      const course = await coursesService.detail(cls.course_id);
      nav("course-detail", { course: { ...course, class_id: cls.class_id, class_name: cls.name } });
    } catch {
      nav("course-detail", {
        course: {
          course_id: cls.course_id,
          title: cls.name,
          description: cls.description,
          difficulty_level: "beginner",
          class_id: cls.class_id,
          class_name: cls.name,
        },
      });
    }
  };

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

  const roleBadge = { student: "role-student", instructor: "role-instructor", admin: "role-admin", system_admin: "role-admin" };

  return (
    <div className="pg">
      <Navbar theme={theme} setTheme={setTheme} user={user} nav={nav} onLogout={onLogout} currentPage={currentPage} currentStreak={currentStreak} />
      <div className="prof-page">

        {/* ── Profile header ── */}
        <div className="prof-card">
          <div className="prof-avatar-lg">{initials}</div>
          <div className="prof-info">
            <h1>{user?.full_name}</h1>
            <p className="prof-email"><I.Mail /> {user?.email}</p>
            <div className="prof-badges">
              <span className={`ud-role ${roleBadge[user?.role] || ""}`}>{capitalize(user?.role || "student")}</span>
              <span className={`sub-badge sub-${userPlan}`}><I.Crown /> {capitalize(userPlan || "free")}</span>
              {user?.is_active && <span className="prof-active"><I.Check /> Active</span>}
            </div>
          </div>
        </div>

        {/* ── Account details + Join class ── */}
        <div className="prof-grid">
          <div className="prof-section">
            <h2>Account Details</h2>
            <div className="prof-details">
              <div className="prof-row"><span>Full Name</span><span>{user?.full_name}</span></div>
              <div className="prof-row"><span>Email</span><span>{user?.email}</span></div>
              <div className="prof-row"><span>Role</span><span>{capitalize(user?.role || "student")}</span></div>
              <div className="prof-row"><span>Email Verified</span><span>{user?.email_verified ? "Yes" : "No"}</span></div>
              <div className="prof-row"><span>Member Since</span><span>{user?.created_at ? new Date(user.created_at).toLocaleDateString() : "—"}</span></div>
              <div className="prof-row"><span>Subscription</span><span className="prof-plan-link" onClick={() => nav("subscription")}>{capitalize(userPlan || "free")} Plan →</span></div>
            </div>
          </div>

          <div className="prof-section">
            <h2>Join a Class</h2>
            <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 16 }}>Enter the class code provided by your instructor</p>
            <div className="prof-join-row">
              <input placeholder="e.g. CYBER-AB3X9K" value={joinCode} onChange={(e) => setJoinCode(e.target.value)} onKeyDown={(e) => e.key === "Enter" && joinClass()} />
              <button className="btn ba2 bs" onClick={joinClass} disabled={joinBusy}>{joinBusy ? "Joining..." : "Join"}</button>
            </div>
            {joinMsg.text && <div className={`afb ${joinMsg.type === "ok" ? "ok" : "no"}`} style={{ marginTop: 10 }}>{joinMsg.text}</div>}
          </div>
        </div>

        {/* ── Certificates ── */}
        <div className="prof-section" style={{ marginTop: 24 }}>
          <div className="prof-cert-header">
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <I.Award />
              <h2 style={{ margin: 0 }}>My Certificates</h2>
              {!certsLoading && certs.length > 0 && (
                <span className="prof-cert-count">{certs.length}</span>
              )}
            </div>
            {!certsLoading && certs.length > 0 && (
              <button className="btn bg bs" style={{ fontSize: 12 }} onClick={() => nav("certificates")}>
                View All <I.Right />
              </button>
            )}
          </div>

          {certsLoading && <div style={{ padding: "24px 0" }}><InlineLoader /></div>}

          {!certsLoading && certs.length === 0 && (
            <div className="prof-cert-empty">
              <div className="prof-cert-empty-icon"><I.Award /></div>
              <div>
                <p style={{ fontWeight: 600, marginBottom: 4 }}>No certificates yet</p>
                <p style={{ fontSize: 12, color: "var(--text-muted)" }}>
                  Complete all tasks in a course to earn a certificate.
                </p>
              </div>
              <button className="btn ba2 bs" onClick={() => nav("courses")} style={{ marginLeft: "auto" }}>
                <I.Layers /> Start Learning
              </button>
            </div>
          )}

          {!certsLoading && certs.length > 0 && (
            <div className="prof-cert-list">
              {certs.slice(0, 4).map((cert) => (
                <ProfileCertCard
                  key={cert.certificate_id}
                  cert={cert}
                  onDownload={handleDownload}
                  downloading={downloading}
                  onView={handleView}
                  viewing={viewing}
                />
              ))}
              {certs.length > 4 && (
                <button
                  className="prof-cert-more"
                  onClick={() => nav("certificates")}
                >
                  +{certs.length - 4} more certificate{certs.length - 4 !== 1 ? "s" : ""} — View All
                </button>
              )}
            </div>
          )}
        </div>

        {/* ── Enrolled Classes ── */}
        <div className="prof-section" style={{ marginTop: 24 }}>
          <h2>Enrolled Classes</h2>
          {classesLoading ? <div className="adm-center"><InlineLoader /></div> : enrolledClasses.length === 0 ? (
            <div className="adm-empty">You're not enrolled in any classes yet. Ask your instructor for a class code.</div>
          ) : (
            <div className="inst-grid">
              {enrolledClasses.map((cls) => (
                <div key={cls.class_id} className="inst-card" onClick={() => openClassCourse(cls)} style={{ cursor: "pointer" }}>
                  <h3>{cls.name}</h3>
                  {cls.description && <p className="inst-desc">{cls.description}</p>}
                  <div className="inst-meta">
                    <span><I.Users /> {cls.student_count} students</span>
                    <span className={cls.is_active ? "adm-pub-yes" : "adm-pub-no"}>{cls.is_active ? "Active" : "Ended"}</span>
                  </div>
                  <button className="btn ba2 bs" style={{ marginTop: 14 }} onClick={(e) => { e.stopPropagation(); openClassCourse(cls); }}>
                    Open Course <I.Right />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
