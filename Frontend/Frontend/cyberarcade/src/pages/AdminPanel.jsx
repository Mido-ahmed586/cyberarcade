import { useEffect, useState, useRef } from "react";
import Navbar from "../components/layout/Navbar";
import I from "../components/icons/Icons";
import { adminService } from "../services/admin.service";
import { coursesService } from "../services/courses.service";
import { certificatesService } from "../services/certificates.service";
import { capitalize } from "../utils/helpers";
import { InlineLoader } from "../components/ui/Loader";
import { FAKE_COURSES } from "../data/fakeCourses";

const TABS = ["stats", "courses", "users", "labs", "audit", "certificates"];

// ── Default blank lab ────────────────────────────────────────────────────────
const blankLab = (idx) => ({
  _id: Date.now() + idx,
  title: "",
  description: "",
  attacker_machine: "",
  victim_machine: "",
  numTasks: 2,
  tasks: [blankTask(0), blankTask(1)],
});

function blankTask(idx) {
  return { _id: Date.now() + idx + Math.random(), title: `Task ${idx + 1}`, instructions: "", expected_answer: "", hints: "" };
}

// ── Stats ────────────────────────────────────────────────────────────────────
function StatsTab({ stats, loading }) {
  if (loading) return <div className="adm-center"><InlineLoader /></div>;
  if (!stats) return null;
  const items = [
    { label: "Total Users",       value: stats.total_users,          color: "var(--navy-light)" },
    { label: "Active Users",      value: stats.active_users,         color: "var(--success)" },
    { label: "Courses",           value: stats.total_courses,        color: "var(--accent-bright)" },
    { label: "Published",         value: stats.published_courses,    color: "var(--warning)" },
    { label: "Labs",              value: stats.total_labs,           color: "var(--navy-light)" },
    { label: "Active Instances",  value: stats.active_lab_instances, color: "var(--success)" },
    { label: "Classes",           value: stats.total_classes,        color: "var(--accent-bright)" },
    { label: "Enrollments",       value: stats.total_enrollments,    color: "var(--warning)" },
  ];
  return (
    <div className="adm-stats-grid">
      {items.map((s, i) => (
        <div key={i} className="adm-stat-card">
          <div className="adm-stat-value" style={{ color: s.color }}>{s.value}</div>
          <div className="adm-stat-label">{s.label}</div>
        </div>
      ))}
    </div>
  );
}

// ── Courses table ────────────────────────────────────────────────────────────
function CoursesTab({ courses, onEdit, onDelete, onAdd, onTogglePublish, loading, onSeedFake }) {
  if (loading) return <div className="adm-center"><InlineLoader /></div>;
  return (
    <>
      <div className="adm-toolbar">
        <h2>Courses ({courses.length})</h2>
        <div style={{ display: "flex", gap: 8 }}>
          {onSeedFake && (
            <button className="btn bg bs" onClick={onSeedFake}><I.Zap /> Seed Demo</button>
          )}
          <button className="btn ba2 bs" onClick={onAdd}><I.Plus /> Add Course</button>
        </div>
      </div>
      {courses.length === 0 ? (
        <div className="adm-empty">No courses yet. Create one to get started.</div>
      ) : (
        <div className="adm-table-wrap">
          <table className="adm-table">
            <thead><tr><th>Title</th><th>Category</th><th>Difficulty</th><th>Labs</th><th>Published</th><th>Actions</th></tr></thead>
            <tbody>
              {courses.map((c) => (
                <tr key={c.course_id}>
                  <td className="adm-td-title">{c.title}</td>
                  <td><span className="adm-badge">{c.category}</span></td>
                  <td><span className={`df d-${c.difficulty_level}`}>{capitalize(c.difficulty_level)}</span></td>
                  <td style={{ fontSize: 13, color: "var(--text-muted)" }}>{c.lab_count ?? "—"}</td>
                  <td>
                    <button className={`adm-toggle ${c.is_published ? "on" : "off"}`} onClick={() => onTogglePublish(c)}>
                      {c.is_published ? "Published" : "Draft"}
                    </button>
                  </td>
                  <td>
                    <div className="adm-actions">
                      <button className="adm-act-btn" onClick={() => onEdit(c)} title="Edit"><I.Edit /></button>
                      <button className="adm-act-btn adm-act-danger" onClick={() => onDelete(c.course_id)} title="Delete"><I.Trash /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}

// ── Users table ──────────────────────────────────────────────────────────────
function UsersTab({ users, loading, onChangeRole, onToggleActive }) {
  const [filter, setFilter] = useState("");
  const list = filter ? users.filter((u) => u.role === filter) : users;
  if (loading) return <div className="adm-center"><InlineLoader /></div>;
  return (
    <>
      <div className="adm-toolbar">
        <h2>Users ({list.length})</h2>
        <div className="adm-filters">
          {["", "student", "instructor", "admin"].map((r) => (
            <button key={r} className={`fl ${filter === r ? "act" : ""}`} onClick={() => setFilter(r)}>{r || "All"}</button>
          ))}
        </div>
      </div>
      <div className="adm-table-wrap">
        <table className="adm-table">
          <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th>Joined</th></tr></thead>
          <tbody>
            {list.map((u) => (
              <tr key={u.user_id}>
                <td className="adm-td-title">{u.full_name}</td>
                <td style={{ color: "var(--text-muted)", fontSize: 13 }}>{u.email}</td>
                <td>
                  <select className="adm-select" value={u.role} onChange={(e) => onChangeRole(u.user_id, e.target.value)}>
                    <option value="student">Student</option>
                    <option value="instructor">Instructor</option>
                    <option value="admin">Admin</option>
                    <option value="system_admin">System Admin</option>
                  </select>
                </td>
                <td>
                  <button className={`adm-toggle ${u.is_active ? "on" : "off"}`} onClick={() => onToggleActive(u)}>
                    {u.is_active ? "Active" : "Inactive"}
                  </button>
                </td>
                <td style={{ fontSize: 11, color: "var(--text-muted)" }}>{new Date(u.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

// ── Lab card inside the modal ────────────────────────────────────────────────
function LabCard({ lab, labIdx, onChange, onRemove, canRemove }) {
  const updateTask  = (ti, field, val) => {
    const tasks = lab.tasks.map((t, i) => i === ti ? { ...t, [field]: val } : t);
    onChange({ ...lab, tasks });
  };
  const addTask     = () => onChange({ ...lab, tasks: [...lab.tasks, blankTask(lab.tasks.length)] });
  const removeTask  = (ti) => onChange({ ...lab, tasks: lab.tasks.filter((_, i) => i !== ti) });

  return (
    <div className="lab-wcard">
      {/* Lab header */}
      <div className="lab-wcard-hdr">
        <span>Lab {labIdx + 1}</span>
        {canRemove && (
          <button className="adm-act-btn adm-act-danger" onClick={onRemove} title="Remove lab" style={{ marginLeft: "auto" }}>
            <I.Trash />
          </button>
        )}
      </div>

      {/* Lab fields */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <div className="fg3" style={{ gridColumn: "1/-1" }}>
          <label>Lab Title</label>
          <input placeholder="e.g. SSH Brute Force Attack" value={lab.title} onChange={(e) => onChange({ ...lab, title: e.target.value })} />
        </div>
        <div className="fg3" style={{ gridColumn: "1/-1" }}>
          <label>Lab Description</label>
          <textarea className="adm-textarea" placeholder="What will students do?" value={lab.description} onChange={(e) => onChange({ ...lab, description: e.target.value })} />
        </div>
        <div className="fg3">
          <label>⚔ Attacker Machine</label>
          <select className="adm-select" value={lab.attacker_machine} onChange={(e) => onChange({ ...lab, attacker_machine: e.target.value })}>
            <option value="">None</option>
            <option value="cyber_kali">cyber_kali (SSH Brute-Force)</option>
            <option value="kali-attacker">kali-attacker (Metasploit)</option>
          </select>
        </div>
        <div className="fg3">
          <label>🎯 Victim Machine</label>
          <select className="adm-select" value={lab.victim_machine} onChange={(e) => onChange({ ...lab, victim_machine: e.target.value })}>
            <option value="">None</option>
            <option value="cyber_target">cyber_target (Ubuntu SSH)</option>
            <option value="metasploitable2">metasploitable2</option>
          </select>
        </div>
      </div>

      {/* Tasks */}
      <div className="lab-wcard-tasks">
        <div className="lab-wcard-tasks-hdr">
          <span>Tasks ({lab.tasks.length})</span>
          <button className="adm-act-btn" onClick={addTask} title="Add task"><I.Plus /></button>
        </div>
        {lab.tasks.map((t, ti) => (
          <div key={t._id} className="task-wcard">
            <div className="task-wcard-hdr">
              <span>Task {ti + 1}</span>
              {lab.tasks.length > 1 && (
                <button className="adm-act-btn adm-act-danger" onClick={() => removeTask(ti)} style={{ marginLeft: "auto" }}><I.Trash /></button>
              )}
            </div>
            <div className="fg3">
              <label>Title</label>
              <input placeholder={`Task ${ti + 1} name`} value={t.title} onChange={(e) => updateTask(ti, "title", e.target.value)} />
            </div>
            <div className="fg3" style={{ marginTop: 8 }}>
              <label>Instructions / Question</label>
              <textarea className="adm-textarea" placeholder="Describe what the student must find or do…" value={t.instructions} onChange={(e) => updateTask(ti, "instructions", e.target.value)} />
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginTop: 8 }}>
              <div className="fg3">
                <label>Expected Answer</label>
                <input placeholder="e.g. 22 or Apache" value={t.expected_answer} onChange={(e) => updateTask(ti, "expected_answer", e.target.value)} />
              </div>
              <div className="fg3">
                <label>Hints (one per line)</label>
                <textarea className="adm-textarea" style={{ minHeight: 56 }} placeholder={"Use nmap -sV\nThe answer is port 22"} value={t.hints} onChange={(e) => updateTask(ti, "hints", e.target.value)} />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Course modal ─────────────────────────────────────────────────────────────
function CourseModal({ show, editing, form, setForm, labs, setLabs, step, onNext, onBack, error, busy, onSave, onClose }) {
  if (!show) return null;
  const isStep2 = !editing && step === 2;

  const addLab    = () => setLabs((p) => [...p, blankLab(p.length)]);
  const removeLab = (idx) => setLabs((p) => p.filter((_, i) => i !== idx));
  const updateLab = (idx, val) => setLabs((p) => p.map((l, i) => i === idx ? val : l));

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className={`modal-box modal-wide`} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{editing ? "Edit Course" : "Create Course"}</h3>
          <button className="ib" onClick={onClose}><I.X /></button>
        </div>

        {/* Step indicator (create only) */}
        {!editing && (
          <div className="modal-steps">
            <div className={`mstep${step >= 1 ? " act" : ""}`}>
              <span className="mstep-n">1</span><span>Course Info</span>
            </div>
            <div className="mstep-line" />
            <div className={`mstep${step >= 2 ? " act" : ""}`}>
              <span className="mstep-n">2</span><span>Labs &amp; Tasks</span>
            </div>
          </div>
        )}

        <div className="modal-body">

          {/* ── Step 1: course metadata ── */}
          {!isStep2 && (
            <>
              <div className="fg3"><label>Course Title</label><input placeholder="e.g. Network Security" value={form.title} onChange={(e) => setForm((p) => ({ ...p, title: e.target.value }))} /></div>
              <div className="fg3"><label>Description</label><textarea className="adm-textarea" placeholder="What will students learn?" value={form.description} onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))} /></div>
              <div className="fg3"><label>Category</label><input placeholder="e.g. Web Security" value={form.category} onChange={(e) => setForm((p) => ({ ...p, category: e.target.value }))} /></div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                <div className="fg3"><label>Difficulty</label>
                  <select className="adm-select" value={form.difficulty_level} onChange={(e) => setForm((p) => ({ ...p, difficulty_level: e.target.value }))}>
                    <option value="beginner">Beginner</option>
                    <option value="intermediate">Intermediate</option>
                    <option value="advanced">Advanced</option>
                  </select>
                </div>
                <div className="fg3"><label>Est. Hours</label><input type="number" placeholder="e.g. 4" value={form.estimated_hours} onChange={(e) => setForm((p) => ({ ...p, estimated_hours: e.target.value }))} /></div>
              </div>
            </>
          )}

          {/* ── Step 2: labs + tasks ── */}
          {isStep2 && (
            <div className="labs-wizard">
              <div className="labs-wizard-hdr">
                <span>{labs.length} Lab{labs.length !== 1 ? "s" : ""}</span>
                <button className="btn ba2 bs" onClick={addLab}><I.Plus /> Add Lab</button>
              </div>
              {labs.map((lab, idx) => (
                <LabCard
                  key={lab._id}
                  lab={lab}
                  labIdx={idx}
                  onChange={(val) => updateLab(idx, val)}
                  onRemove={() => removeLab(idx)}
                  canRemove={labs.length > 1}
                />
              ))}
            </div>
          )}

          {error && <div className="ae" style={{ marginTop: 12 }}>{error}</div>}
        </div>

        <div className="modal-footer">
          {isStep2 ? (
            <>
              <button className="btn bg bs" onClick={onBack}>← Back</button>
              <button className="btn ba2 bs" onClick={onSave} disabled={busy}>
                {busy ? "Creating…" : `Create Course (${labs.length} lab${labs.length !== 1 ? "s" : ""})`}
              </button>
            </>
          ) : editing ? (
            <>
              <button className="btn bg bs" onClick={onClose}>Cancel</button>
              <button className="btn ba2 bs" onClick={onSave} disabled={busy}>{busy ? "Saving…" : "Update"}</button>
            </>
          ) : (
            <>
              <button className="btn bg bs" onClick={onClose}>Cancel</button>
              <button className="btn ba2 bs" onClick={onNext}>Next: Add Labs →</button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Certificates tab ──────────────────────────────────────────────────────────
function CertificatesTab() {
  // ── Verification ──
  const [serial, setSerial]   = useState("");
  const [vResult, setVResult] = useState(null);
  const [vBusy, setVBusy]     = useState(false);
  const [vError, setVError]   = useState("");

  const handleVerify = async () => {
    const s = serial.trim().toUpperCase();
    if (!s) return;
    setVBusy(true); setVResult(null); setVError("");
    try { setVResult(await certificatesService.verify(s)); }
    catch (e) { setVError(e.message || "Verification failed."); }
    finally { setVBusy(false); }
  };

  // ── Certificate list ──
  const [certs, setCerts]       = useState([]);
  const [certsLoading, setCL]   = useState(true);
  const [revoking, setRevoking] = useState(null);
  const [toast, setToast]       = useState("");

  const showToast = (m) => { setToast(m); setTimeout(() => setToast(""), 3000); };

  useEffect(() => {
    certificatesService.adminList()
      .then(setCerts).catch(() => {}).finally(() => setCL(false));
  }, []);

  const handleRevoke = async (cert) => {
    if (!confirm(`Revoke certificate ${cert.serial_number}? This cannot be undone.`)) return;
    setRevoking(cert.certificate_id);
    try {
      const updated = await certificatesService.adminRevoke(cert.certificate_id);
      setCerts((p) => p.map((c) => c.certificate_id === updated.certificate_id ? updated : c));
      showToast("Certificate revoked.");
    } catch (e) { showToast("Error: " + e.message); }
    finally { setRevoking(null); }
  };

  const fmtDate = (iso) => iso ? new Date(iso).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" }) : "—";

  return (
    <div className="adm-cert-tab">
      {/* ── Verification panel ── */}
      <div className="adm-cert-verify-panel">
        <h2 className="adm-cert-section-title"><I.Hash /> Certificate Verification</h2>
        <p style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 16 }}>
          Enter a serial number to instantly verify any CyberArcade certificate.
        </p>
        <div className="adm-cert-verify-row">
          <input
            className="adm-cert-serial-input"
            placeholder="CYAC-XXXX-XXXX-XXXX-XXXX"
            value={serial}
            onChange={(e) => setSerial(e.target.value.toUpperCase())}
            onKeyDown={(e) => e.key === "Enter" && handleVerify()}
            spellCheck={false}
          />
          <button className="btn ba2 bs" onClick={handleVerify} disabled={vBusy || !serial.trim()}>
            {vBusy ? <span className="cert-spinner" /> : <I.Search />}
            Verify
          </button>
        </div>

        {vError && (
          <div className="ae" style={{ marginTop: 12 }}><I.AlertTriangle /> {vError}</div>
        )}

        {vResult && (
          <div className={`adm-cert-verify-result ${vResult.valid ? "valid" : "invalid"}`}>
            {vResult.valid ? (
              <>
                <span className="adm-cvr-icon valid"><I.Check /></span>
                <div className="adm-cvr-body">
                  <div className="adm-cvr-title">✓ Valid Certificate</div>
                  <div className="adm-cvr-grid">
                    <span>Student</span><strong>{vResult.student_name}</strong>
                    <span>Course</span><strong>{vResult.course_name}</strong>
                    <span>Issued</span><strong>{fmtDate(vResult.issued_at)}</strong>
                    <span>Serial</span><code>{vResult.serial_number}</code>
                  </div>
                </div>
              </>
            ) : (
              <>
                <span className="adm-cvr-icon invalid"><I.X /></span>
                <div className="adm-cvr-body">
                  <div className="adm-cvr-title">✕ Invalid Certificate</div>
                  <div style={{ color: "var(--text-muted)", fontSize: 13 }}>{vResult.message}</div>
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {/* ── All certificates table ── */}
      <div style={{ marginTop: 32 }}>
        <h2 className="adm-cert-section-title"><I.Award /> Issued Certificates ({certs.length})</h2>
        {certsLoading ? (
          <div className="adm-center"><InlineLoader /></div>
        ) : certs.length === 0 ? (
          <div className="adm-empty">No certificates have been issued yet.</div>
        ) : (
          <div className="adm-table-wrap">
            <table className="adm-table">
              <thead>
                <tr>
                  <th>Student</th>
                  <th>Course</th>
                  <th>Serial Number</th>
                  <th>Issued</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {certs.map((c) => (
                  <tr key={c.certificate_id}>
                    <td style={{ fontWeight: 600 }}>{c.student_name}</td>
                    <td style={{ color: "var(--text-secondary)", fontSize: 13 }}>{c.course_name}</td>
                    <td>
                      <code style={{ fontSize: 11, color: "var(--accent-bright)", background: "var(--accent-surface)", padding: "2px 6px", borderRadius: 4 }}>
                        {c.serial_number}
                      </code>
                    </td>
                    <td style={{ fontSize: 12, color: "var(--text-muted)" }}>{fmtDate(c.issued_at)}</td>
                    <td>
                      <span className={`adm-badge ${c.verification_status === "valid" ? "" : "adm-badge-danger"}`}>
                        {c.verification_status}
                      </span>
                    </td>
                    <td>
                      {c.verification_status === "valid" && (
                        <button
                          className="btn bg bs"
                          style={{ fontSize: 11, padding: "4px 10px", color: "var(--danger)" }}
                          onClick={() => handleRevoke(c)}
                          disabled={revoking === c.certificate_id}
                        >
                          <I.X /> Revoke
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      {toast && <div className="toast-msg">{toast}</div>}
    </div>
  );
}

// ── Main AdminPanel ──────────────────────────────────────────────────────────
export default function AdminPanel({ theme, setTheme, user, nav, onLogout, currentPage, currentStreak }) {
  const [tab, setTab]               = useState("stats");
  const [stats, setStats]           = useState(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [courses, setCourses]       = useState([]);
  const coursesLoaded               = useRef(false);
  const [coursesLoading, setCoursesLoading] = useState(false);
  const [users, setUsers]           = useState([]);
  const usersLoaded                 = useRef(false);
  const [usersLoading, setUsersLoading]   = useState(false);
  const [auditLogs, setAuditLogs]   = useState([]);
  const auditLoaded                 = useRef(false);
  const [auditLoading, setAuditLoading]   = useState(false);

  const [showModal, setShowModal]   = useState(false);
  const [editingCourse, setEditingCourse] = useState(null);
  const [courseForm, setCourseForm] = useState({ title: "", description: "", difficulty_level: "beginner", category: "", estimated_hours: "" });
  const [labForms, setLabForms]     = useState([blankLab(0)]);
  const [courseStep, setCourseStep] = useState(1);
  const [courseError, setCourseError] = useState("");
  const [courseBusy, setCourseBusy] = useState(false);
  const [toast, setToast]           = useState("");

  const showToast = (m) => { setToast(m); setTimeout(() => setToast(""), 3500); };

  const seedFakeCourses = () => { setCourses((prev) => { const existingIds = new Set(prev.map(c => c.course_id)); const toAdd = FAKE_COURSES.filter(c => !existingIds.has(c.course_id)); return [...prev, ...toAdd]; }); showToast(`Demo courses added`); };

  // Stats — load once
  useEffect(() => {
    adminService.getStats().then(setStats).catch(() => {}).finally(() => setStatsLoading(false));
  }, []);

  // Tab data — load once per tab, never overwrite if already loaded
  useEffect(() => {
    if (tab === "courses" && !coursesLoaded.current) {
      coursesLoaded.current = true;
      setCoursesLoading(true);
      coursesService.list({ per_page: 50 })
        .then((data) => setCourses(data || []))
        .catch(() => {})
        .finally(() => setCoursesLoading(false));
    }
    if (tab === "users" && !usersLoaded.current) {
      usersLoaded.current = true;
      setUsersLoading(true);
      adminService.listUsers({ per_page: 100 })
        .then((data) => setUsers(data || []))
        .catch(() => {})
        .finally(() => setUsersLoading(false));
    }
    if (tab === "audit" && !auditLoaded.current) {
      auditLoaded.current = true;
      setAuditLoading(true);
      adminService.getAuditLog({ per_page: 50 })
        .then((data) => setAuditLogs(data || []))
        .catch(() => {})
        .finally(() => setAuditLoading(false));
    }
  }, [tab]);

  // ── Open add modal ───────────────────────────────────────────────────────
  const openAdd = () => {
    setEditingCourse(null);
    setCourseForm({ title: "", description: "", difficulty_level: "beginner", category: "", estimated_hours: "" });
    setLabForms([blankLab(0)]);
    setCourseStep(1);
    setCourseError("");
    setShowModal(true);
  };

  const openEdit = (c) => {
    setEditingCourse(c);
    setCourseForm({ title: c.title, description: c.description, difficulty_level: c.difficulty_level, category: c.category, estimated_hours: c.estimated_hours || "" });
    setCourseStep(1);
    setCourseError("");
    setShowModal(true);
  };

  // ── Step navigation ──────────────────────────────────────────────────────
  const goToStep2 = () => {
    setCourseError("");
    if (!courseForm.title.trim() || !courseForm.description.trim() || !courseForm.category.trim()) {
      setCourseError("Course title, description, and category are required.");
      return;
    }
    setCourseStep(2);
  };

  // ── Save ─────────────────────────────────────────────────────────────────
  const saveCourse = async () => {
    setCourseError("");

    if (!courseForm.title.trim() || !courseForm.description.trim() || !courseForm.category.trim()) {
      setCourseError("All course fields are required.");
      return;
    }

    setCourseBusy(true);
    try {
      const payload = {
        ...courseForm,
        estimated_hours: courseForm.estimated_hours ? Number(courseForm.estimated_hours) : null,
      };

      // ── Edit existing course (metadata only) ──────────────────────────
      if (editingCourse) {
        const updated = await adminService.updateCourse(editingCourse.course_id, payload);
        // Patch only this course in the list — don't replace the whole array
        setCourses((prev) => prev.map((c) =>
          c.course_id === editingCourse.course_id ? { ...c, ...updated } : c
        ));
        showToast("Course updated");
        setShowModal(false);
        return;
      }

      // ── Create new course ────────────────────────────────────────────
      // Validate all labs
      for (let li = 0; li < labForms.length; li++) {
        const lab = labForms[li];
        if (!lab.title.trim()) { setCourseError(`Lab ${li + 1}: title is required.`); return; }
        for (let ti = 0; ti < lab.tasks.length; ti++) {
          const t = lab.tasks[ti];
          if (!t.title.trim() || !t.instructions.trim()) {
            setCourseError(`Lab ${li + 1} → Task ${ti + 1}: title and instructions are required.`);
            return;
          }
        }
      }

      // 1. Create course
      const course = await adminService.createCourse(payload);

      // 2. Create each lab + its tasks + hints
      for (let li = 0; li < labForms.length; li++) {
        const lf = labForms[li];

        const svcs = {};
        if (lf.attacker_machine) svcs.attacker = { image: lf.attacker_machine };
        if (lf.victim_machine)   svcs.victim   = { image: lf.victim_machine };
        if (Object.keys(svcs).length === 0) svcs.victim = { image: "kali:latest" };

        const lab = await adminService.createLab({
          course_id: course.course_id,
          title: lf.title,
          description: lf.description || lf.title,
          difficulty: courseForm.difficulty_level,
          docker_compose_config: { services: svcs },
          has_auto_solve: false,
          max_duration_minutes: 120,
          sort_order: li,
        });

        await adminService.updateLab(lab.lab_id, { is_published: true });

        for (let ti = 0; ti < lf.tasks.length; ti++) {
          const tf = lf.tasks[ti];
          const task = await adminService.createTask(lab.lab_id, {
            title: tf.title.trim(),
            instructions: tf.instructions.trim(),
            expected_answer: tf.expected_answer.trim() || null,
            sort_order: ti,
          });
          if (tf.hints.trim()) {
            const lines = tf.hints.split("\n").map((h) => h.trim()).filter(Boolean);
            for (let h = 0; h < lines.length; h++) {
              await adminService.createHint(lab.lab_id, task.task_id, {
                hint_text: lines[h],
                hint_order: h + 1,
                delay_minutes: 5,
              });
            }
          }
        }
      }

      // 3. Publish course
      await adminService.updateCourse(course.course_id, { is_published: true });

      // 4. Prepend to list — never replace existing courses
      setCourses((prev) => [{ ...course, is_published: true, lab_count: labForms.length }, ...prev]);
      showToast(`"${course.title}" created with ${labForms.length} lab${labForms.length !== 1 ? "s" : ""}!`);
      setShowModal(false);

    } catch (e) {
      setCourseError(e.message || "Failed to save course");
    } finally {
      setCourseBusy(false);
    }
  };

  // ── Delete / toggle ──────────────────────────────────────────────────────
  const delCourse = async (id) => {
    if (!confirm("Delete this course? This cannot be undone.")) return;
    try {
      await adminService.deleteCourse(id);
      setCourses((prev) => prev.filter((c) => c.course_id !== id));
      showToast("Course deleted");
    } catch (e) { showToast("Error: " + e.message); }
  };

  const togglePublish = async (course) => {
    try {
      const updated = await adminService.updateCourse(course.course_id, { is_published: !course.is_published });
      setCourses((prev) => prev.map((c) =>
        c.course_id === course.course_id ? { ...c, is_published: !course.is_published, ...updated } : c
      ));
      showToast(course.is_published ? "Course unpublished" : "Course published");
    } catch (e) { showToast("Error: " + e.message); }
  };

  const changeRole = async (id, role) => {
    try { await adminService.updateUserRole(id, role); setUsers((p) => p.map((u) => u.user_id === id ? { ...u, role } : u)); showToast("Role updated"); }
    catch (e) { showToast("Error: " + e.message); }
  };

  const toggleActive = async (u) => {
    try { await adminService.updateUserStatus(u.user_id, !u.is_active); setUsers((p) => p.map((x) => x.user_id === u.user_id ? { ...x, is_active: !u.is_active } : x)); showToast(u.is_active ? "Deactivated" : "Activated"); }
    catch (e) { showToast("Error: " + e.message); }
  };

  return (
    <div className="pg">
      <Navbar theme={theme} setTheme={setTheme} user={user} nav={nav} onLogout={onLogout} currentPage={currentPage} currentStreak={currentStreak} />
      <div className="adm-page">
        <div className="adm-header">
          <h1><I.Settings /> Admin <span className="he">Panel</span></h1>
          <p>Manage courses, users, labs, and analytics</p>
        </div>
        <div className="adm-tabs">
          {TABS.map((t) => (
            <button key={t} className={`adm-tab ${tab === t ? "act" : ""}`} onClick={() => setTab(t)}>{capitalize(t)}</button>
          ))}
        </div>

        {tab === "stats"   && <StatsTab stats={stats} loading={statsLoading} />}
        {tab === "courses" && <CoursesTab courses={courses} loading={coursesLoading} onAdd={openAdd} onEdit={openEdit} onDelete={delCourse} onTogglePublish={togglePublish} onSeedFake={seedFakeCourses} />}
        {tab === "users"   && <UsersTab users={users} loading={usersLoading} onChangeRole={changeRole} onToggleActive={toggleActive} />}
        {tab === "audit"   && (
          auditLoading
            ? <div className="adm-center"><InlineLoader /></div>
            : auditLogs.length === 0
              ? <div className="adm-empty">No audit entries.</div>
              : <div className="adm-table-wrap"><table className="adm-table"><thead><tr><th>Time</th><th>Action</th><th>Target</th></tr></thead><tbody>{auditLogs.map((l) => <tr key={l.log_id}><td style={{fontSize:12,color:"var(--text-muted)"}}>{new Date(l.created_at).toLocaleString()}</td><td><span className="adm-badge">{l.action}</span></td><td style={{fontSize:12}}>{l.target_type||"—"}</td></tr>)}</tbody></table></div>
        )}
        {tab === "labs"         && <div className="adm-empty">Use the Courses tab to manage labs per course.</div>}
        {tab === "certificates" && <CertificatesTab />}
      </div>

      <CourseModal
        show={showModal}
        editing={editingCourse}
        form={courseForm}
        setForm={setCourseForm}
        labs={labForms}
        setLabs={setLabForms}
        step={courseStep}
        onNext={goToStep2}
        onBack={() => setCourseStep(1)}
        error={courseError}
        busy={courseBusy}
        onSave={saveCourse}
        onClose={() => setShowModal(false)}
      />

      {toast && <div className="toast-msg">{toast}</div>}
    </div>
  );
}