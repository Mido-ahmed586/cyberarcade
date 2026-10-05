import { useEffect, useState, useMemo } from "react";
import Navbar from "../components/layout/Navbar";
import I from "../components/icons/Icons";
import { coursesService } from "../services/courses.service";
import { capitalize, formatHours } from "../utils/helpers";
import { InlineLoader } from "../components/ui/Loader";
import { FAKE_COURSES } from "../data/fakeCourses";

const isUUID = (id) =>
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id || "");

export default function Courses({ theme, setTheme, user, nav, onLogout, currentPage, currentStreak }) {
  const [courses, setCourses]       = useState([]);
  const [status, setStatus]         = useState("loading");
  const [error, setError]           = useState("");
  const [filter, setFilter]         = useState("All");
  const [progressMap, setProgressMap] = useState({});

  useEffect(() => {
    let cancelled = false;
    setStatus("loading");
    coursesService.list({ per_page: 50 })
      .then((data) => {
        if (cancelled) return;
        const real   = data || [];
        const realTitles = new Set(real.map((c) => c.title));
        const extras = FAKE_COURSES.filter((c) => !realTitles.has(c.title));
        setCourses([...real, ...extras]);
        setStatus("ready");
        // Load progress for real courses in parallel
        const realCourses = real.filter((c) => isUUID(c.course_id));
        Promise.all(
          realCourses.map((c) =>
            coursesService.myProgress(c.course_id)
              .then((p) => ({ id: c.course_id, data: p }))
              .catch(() => ({ id: c.course_id, data: null }))
          )
        ).then((results) => {
          if (cancelled) return;
          const map = {};
          results.forEach((r) => { if (r.data) map[r.id] = r.data; });
          setProgressMap(map);
        });
      })
      .catch(() => {
        if (cancelled) return;
        setCourses(FAKE_COURSES);
        setStatus("ready");
      });
    return () => { cancelled = true; };
  }, []);

  const categories = useMemo(
    () => ["All", ...Array.from(new Set(courses.map((c) => c.category)))],
    [courses]
  );
  const list = useMemo(() => {
    const filtered = filter === "All" ? courses : courses.filter((c) => c.category === filter);
    return [...filtered].sort((a, b) => {
      if (a.title === "Network Security") return -1;
      if (b.title === "Network Security") return 1;
      return 0;
    });
  }, [filter, courses]);

  return (
    <div className="pg">
      <Navbar theme={theme} setTheme={setTheme} user={user} nav={nav} onLogout={onLogout} currentPage={currentPage} currentStreak={currentStreak} />
      <div className="cop">
        <div className="coh">
          <h1>Cyber<span className="he">security</span> Modules</h1>
          <p>
            {status === "ready"
              ? `${list.length} of ${courses.length} courses`
              : status === "loading"
              ? "Loading modules..."
              : "Unable to load modules"}
          </p>
        </div>

        {status === "error" && <div className="ae" style={{ marginBottom: 16 }}>{error}</div>}
        {status === "loading" && (
          <div style={{ display:"flex",justifyContent:"center",padding:40 }}><InlineLoader /></div>
        )}
        {status === "ready" && courses.length === 0 && (
          <div className="empty-state"><p>No published courses yet.</p></div>
        )}

        {status === "ready" && courses.length > 0 && (
          <>
            <div className="fr">
              {categories.map((c) => (
                <button key={c} className={`fl ${filter === c ? "act" : ""}`} onClick={() => setFilter(c)}>{c}</button>
              ))}
            </div>

            <div className="course-grid">
              {list.map((c, i) => {
                const prog = progressMap[c.course_id];
                const pct  = prog?.percent        ?? 0;
                const done = prog?.completed_labs ?? 0;
                const tot  = prog?.total_labs     ?? (c.lab_count ?? 0);

                return (
                  <div
                    key={c.course_id}
                    className={`course-tile${done > 0 && done === tot && tot > 0 ? " course-tile-complete" : ""}`}
                    style={{ animationDelay: `${i * 0.06}s` }}
                    onClick={() => nav("course-detail", { course: c })}
                  >
                    {/* Completion badge */}
                    {done > 0 && done === tot && tot > 0 && (
                      <div className="course-tile-complete-badge" title="Course Complete">✓</div>
                    )}

                    {/* Resting face */}
                    <div className="course-tile-front">
                      <span className={`df d-${c.difficulty_level}`}>{capitalize(c.difficulty_level)}</span>
                      <h3>{c.title}</h3>
                      <div className="course-tile-meta">
                        <span className="cca">{c.category}</span>
                        <span className="mi"><I.Clock /> {formatHours(c.estimated_hours)}</span>
                      </div>
                      {/* Progress mini-bar (only for courses with progress data) */}
                      {tot > 0 && (
                        <div className="course-tile-prog">
                          <div className="course-tile-prog-bar">
                            <div className="course-tile-prog-fill" style={{ width: `${pct}%` }} />
                          </div>
                          <div className="course-tile-prog-label">
                            <span>{done}/{tot} Labs</span>
                            <span>{pct}%</span>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Hover overlay */}
                    <div className="course-tile-hover">
                      <div className="course-tile-stats">
                        <div className="course-stat">
                          <span className="course-stat-num">{c.lab_count ?? tot ?? 0}</span>
                          <span className="course-stat-label">{(c.lab_count ?? 0) === 1 ? "Lab" : "Labs"}</span>
                        </div>
                        <div className="course-stat">
                          <span className="course-stat-num">{formatHours(c.estimated_hours)}</span>
                          <span className="course-stat-label">Duration</span>
                        </div>
                        {tot > 0 && (
                          <div className="course-stat">
                            <span className="course-stat-num">{pct}%</span>
                            <span className="course-stat-label">Progress</span>
                          </div>
                        )}
                      </div>
                      <p className="course-tile-desc">{c.description}</p>
                      <button className="btn ba2 bf course-enroll-btn">
                        {done > 0 ? "Continue →" : "Start Course →"}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
