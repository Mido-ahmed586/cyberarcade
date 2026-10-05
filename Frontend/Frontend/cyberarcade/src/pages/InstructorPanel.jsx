import { useEffect, useState } from "react";
import Navbar from "../components/layout/Navbar";
import I from "../components/icons/Icons";
import { classesService } from "../services/classes.service";
import { coursesService } from "../services/courses.service";
import { InlineLoader } from "../components/ui/Loader";

export default function InstructorPanel({ theme, setTheme, user, nav, onLogout, currentPage, currentStreak }) {
  const [tab, setTab] = useState("classes");
  const [classes, setClasses] = useState([]);
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ course_id: "", name: "", description: "", max_students: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");
  const [selectedClass, setSelectedClass] = useState(null);
  const [progress, setProgress] = useState([]);
  const [progressLoading, setProgressLoading] = useState(false);
  const [copied, setCopied] = useState("");

  const showToast = (m) => { setToast(m); setTimeout(() => setToast(""), 3000); };

  useEffect(() => {
    Promise.all([
      classesService.myClasses().catch(() => []),
      coursesService.list({ per_page: 50 }).catch(() => []),
    ]).then(([cls, crs]) => {
      setClasses(cls || []);
      setCourses(crs || []);
    }).finally(() => setLoading(false));
  }, []);

  const createClass = async () => {
    setError("");
    if (!form.course_id || !form.name) { setError("Course and name are required."); return; }
    setBusy(true);
    try {
      const payload = { ...form, max_students: form.max_students ? Number(form.max_students) : null };
      const created = await classesService.create(payload);
      setClasses((p) => [created, ...p]);
      setShowCreate(false);
      setForm({ course_id: "", name: "", description: "", max_students: "" });
      showToast("Class created! Code: " + created.class_code);
    } catch (e) { setError(e.message || "Failed to create class"); }
    finally { setBusy(false); }
  };

  const viewProgress = async (cls) => {
    setSelectedClass(cls);
    setTab("progress");
    setProgressLoading(true);
    try {
      const data = await classesService.classProgress(cls.class_id);
      setProgress(data || []);
    } catch { setProgress([]); }
    finally { setProgressLoading(false); }
  };

  const copyCode = (code) => {
    navigator.clipboard.writeText(code).then(() => { setCopied(code); setTimeout(() => setCopied(""), 2000); });
  };

  const getCourseName = (id) => courses.find((c) => c.course_id === id)?.title || "—";

  return (
    <div className="pg">
      <Navbar theme={theme} setTheme={setTheme} user={user} nav={nav} onLogout={onLogout} currentPage={currentPage} currentStreak={currentStreak} />
      <div className="adm-page">
        <div className="adm-header">
          <h1><I.Users /> Instructor <span className="he">Panel</span></h1>
          <p>Create classes, share codes with students, and track their progress</p>
        </div>

        <div className="adm-tabs">
          <button className={`adm-tab ${tab === "classes" ? "act" : ""}`} onClick={() => setTab("classes")}>My Classes</button>
          <button className={`adm-tab ${tab === "progress" ? "act" : ""}`} onClick={() => { if (selectedClass) setTab("progress"); }}>Student Progress</button>
        </div>

        {tab === "classes" && (
          <>
            <div className="adm-toolbar">
              <h2>My Classes ({classes.length})</h2>
              <button className="btn ba2 bs" onClick={() => setShowCreate(true)}><I.Plus /> Create Class</button>
            </div>

            {loading ? <div className="adm-center"><InlineLoader /></div> : classes.length === 0 ? (
              <div className="adm-empty">You haven't created any classes yet. Create one and share the code with your students.</div>
            ) : (
              <div className="inst-grid">
                {classes.map((cls) => (
                  <div key={cls.class_id} className="inst-card">
                    <div className="inst-card-top">
                      <h3>{cls.name}</h3>
                      <span className={`adm-toggle ${cls.is_active ? "on" : "off"}`}>{cls.is_active ? "Active" : "Inactive"}</span>
                    </div>
                    {cls.description && <p className="inst-desc">{cls.description}</p>}
                    <div className="inst-meta">
                      <span><I.Book /> {getCourseName(cls.course_id)}</span>
                      <span><I.Users /> {cls.student_count} students</span>
                    </div>
                    <div className="inst-code-row">
                      <span className="inst-code">{cls.class_code}</span>
                      <button className="adm-act-btn" onClick={() => copyCode(cls.class_code)} title="Copy code">
                        {copied === cls.class_code ? <I.Check /> : <I.Copy />}
                      </button>
                    </div>
                    <button className="btn bg bs" style={{ width: "100%", marginTop: 10 }} onClick={() => viewProgress(cls)}>
                      <I.BarChart /> View Progress
                    </button>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {tab === "progress" && selectedClass && (
          <>
            <div className="adm-toolbar">
              <h2>Progress: {selectedClass.name}</h2>
              <button className="btn bg bs" onClick={() => setTab("classes")}><I.Left /> Back</button>
            </div>
            {progressLoading ? <div className="adm-center"><InlineLoader /></div> : progress.length === 0 ? (
              <div className="adm-empty">No students enrolled yet, or no progress data available.</div>
            ) : (
              <div className="adm-table-wrap">
                <table className="adm-table">
                  <thead><tr><th>Student</th><th>Tasks Done</th><th>Auto-Solved</th><th>Attempted</th><th>Hints Used</th></tr></thead>
                  <tbody>
                    {progress.map((p) => (
                      <tr key={p.student_id}>
                        <td className="adm-td-title">{p.student_name}</td>
                        <td><span className="adm-pub-yes">{p.tasks_completed}</span></td>
                        <td>{p.tasks_auto_solved}</td>
                        <td>{p.total_tasks_attempted}</td>
                        <td>{p.total_hints_used}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </div>

      {showCreate && (
        <div className="modal-overlay" onClick={() => setShowCreate(false)}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header"><h3>Create Class</h3><button className="ib" onClick={() => setShowCreate(false)}><I.X /></button></div>
            <div className="modal-body">
              <div className="fg3"><label>Course</label>
                <select className="adm-select" value={form.course_id} onChange={(e) => setForm((p) => ({ ...p, course_id: e.target.value }))}>
                  <option value="">Select a course...</option>
                  {courses.map((c) => <option key={c.course_id} value={c.course_id}>{c.title}</option>)}
                </select>
              </div>
              <div className="fg3"><label>Class Name</label><input placeholder="e.g. Section A — Spring 2025" value={form.name} onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))} /></div>
              <div className="fg3"><label>Description (optional)</label><input placeholder="Description" value={form.description} onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))} /></div>
              <div className="fg3"><label>Max Students (optional)</label><input type="number" placeholder="e.g. 30" value={form.max_students} onChange={(e) => setForm((p) => ({ ...p, max_students: e.target.value }))} /></div>
              {error && <div className="ae">{error}</div>}
            </div>
            <div className="modal-footer">
              <button className="btn bg bs" onClick={() => setShowCreate(false)}>Cancel</button>
              <button className="btn ba2 bs" onClick={createClass} disabled={busy}>{busy ? "Creating..." : "Create"}</button>
            </div>
          </div>
        </div>
      )}

      {toast && <div className="toast-msg">{toast}</div>}
    </div>
  );
}
