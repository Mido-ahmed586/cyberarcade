import { useState, useEffect, useRef, useMemo, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import I from "../components/icons/Icons";
import { CyberLoader } from "../components/ui/Loader";
import Chat from "../components/layout/Chat";
import { labsService } from "../services/labs.service";
import { coursesService } from "../services/courses.service";
import { certificatesService } from "../services/certificates.service";
import { scenariosService } from "../services/scenarios.service";
import { formatCountdown } from "../utils/helpers";
import { TOKEN_KEY } from "../services/api";
import LabTerminal from "../components/LabTerminal";
import TaskHints from "../components/TaskHints";

const RUNTIME_BASE = `${import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"}/api/labs/runtime`;

const ENV_META = {
  none:      { label: "No Environment", icon: "📋", color: "#555",   desc: "Essay / theory only" },
  terminal:  { label: "Terminal",        icon: "⌨️",  color: "#00ff66", desc: "Single Kali terminal" },
  dual:      { label: "Dual Terminal",   icon: "⚔️",  color: "#f59e0b", desc: "Attacker + Defender terminals" },
  "df-kali": { label: "Forensics Kali",  icon: "🔬",  color: "#a78bfa", desc: "Kali Linux with forensics tools" },
};

// ── localStorage helpers for per-lab state persistence ────────────────────────
const saveLabState = (labId, state) => {
  try {
    localStorage.setItem(`lab:${labId}`, JSON.stringify(state));
  } catch {}
};

const loadLabState = (labId) => {
  try {
    const raw = localStorage.getItem(`lab:${labId}`);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

export default function Lab({ theme, setTheme, user, lab, nav, onLogout, chatOpen, setChatOpen, onGamiRewards }) {
  const [detail, setDetail]           = useState(null);
  const [instance, setInstance]       = useState(null);
  const [runtimeStatus, setRuntimeStatus] = useState("stopped");
  const [runtimeMessage, setRuntimeMessage] = useState("");

  const [guacUrlA, setGuacUrlA] = useState(null);
  const [guacUrlB, setGuacUrlB] = useState(null);
  const [activeTermTab, setActiveTermTab] = useState("A");
  const [machineInfo, setMachineInfo] = useState(null); // { attacker, target }

  const [vmOpen, setVmOpen]       = useState(false);
  const [sessionSecs, setSessionSecs] = useState(3600);
  const sessionTimerRef = useRef(null);

  const [loadStatus, setLoadStatus] = useState("loading");
  const [loadError, setLoadError]   = useState("");

  const [hintsByTask,    setHintsByTask]    = useState({});
  const [hintMetaByTask, setHintMetaByTask] = useState({});
  // Global hint cooldown — ONE shared timer across ALL tasks in this lab
  const [globalCountdown, setGlobalCountdown] = useState(0);
  const globalCooldownEndsAt = useRef(null); // absolute ms timestamp
  const [hasGlobalCooldown, setHasGlobalCooldown] = useState(false);
  const [hintBusyByTask, setHintBusyByTask] = useState({});

  const [answersByTask, setAnswersByTask]   = useState({});
  const [resultsByTask, setResultsByTask]   = useState({});

  // Lab-level autosolve (single button at bottom)
  const [labAutosolve, setLabAutosolve] = useState({ busy: false, done: false, error: "" });
  const [autosolveCurrentTask, setAutosolveCurrentTask] = useState(null); // task_id being executed
  const [autofillingTasks, setAutofillingTasks] = useState(new Set()); // task_ids currently being typed
  const typingTimeoutsRef = useRef({});

  const [siblingLabs, setSiblingLabs] = useState([]);
  const [certEarned, setCertEarned]   = useState(false);
  const allCorrectInitRef = useRef(null);

  const [pendingBadges, setPendingBadges] = useState([]);
  const [badgeCelebration, setBadgeCelebration] = useState(null); // badges to celebrate // null = not yet seeded after load

  const isScenarioLab = Boolean(lab?.isScenario || String(lab?.lab_id || "").startsWith("scenario:"));

  const runtimeSlug   = detail?.runtime?.slug || detail?.docker_compose_config?.runtime_slug || null;
  const terminalType  =
    detail?.terminal_type ||
    detail?.runtime?.terminal_type ||
    detail?.docker_compose_config?.terminal_type ||
    (runtimeSlug === "df-kali" ? "df-kali" : null);
  const isDual   = terminalType === "dual";
  const isDfKali = terminalType === "df-kali";
  const envReq   = detail?.env_requirement ||
    (runtimeSlug === "df-kali" ? "df-kali" : runtimeSlug === "ssh-bruteforce" ? "dual" : runtimeSlug ? "terminal" : "none");

  // Session countdown
  useEffect(() => {
    if (vmOpen) {
      setSessionSecs(3600);
      sessionTimerRef.current = setInterval(() => setSessionSecs((s) => s > 0 ? s - 1 : 0), 1000);
    } else {
      clearInterval(sessionTimerRef.current);
    }
    return () => clearInterval(sessionTimerRef.current);
  }, [vmOpen]);

  // ── Load lab detail + progress ─────────────────────────────────────────────
  useEffect(() => {
    // Reset VM/terminal state whenever the active lab changes so that
    // navigating lab-to-lab (same page, component stays mounted) never
    // carries over a stale open terminal from the previous lab.
    setVmOpen(false);
    setGuacUrlA(null);
    setGuacUrlB(null);
    setRuntimeStatus("stopped");
    setRuntimeMessage("");
    setDetail(null);
    setInstance(null);
    setMachineInfo(null);
    setLoadStatus("loading");

    if (isScenarioLab) {
      try {
        const scenarioDetail = scenariosService.detail(lab.scenario_id || lab.lab_id);
        setDetail(scenarioDetail);
        setInstance(null);
        setSiblingLabs(scenariosService.labsByCategory(lab.courseCategory || "Network Security"));
        setRuntimeStatus("stopped");
        // Restore global hint cooldown from localStorage (scenario labs have no server state)
        try {
          const stored = localStorage.getItem(`hint-cooldown:${lab.lab_id}`);
          if (stored) {
            const endsAt = parseInt(stored, 10);
            const rem = Math.max(0, Math.ceil((endsAt - Date.now()) / 1000));
            if (rem > 0) {
              globalCooldownEndsAt.current = endsAt;
              setGlobalCountdown(rem);
              setHasGlobalCooldown(true);
            }
          }
        } catch {}
        setLoadStatus("ready");
      } catch (e) {
        setLoadStatus("error");
        setLoadError(e.message || "Failed to load scenario.");
      }
      return;
    }

    if (!lab?.lab_id) {
      setLoadStatus("error");
      setLoadError("No lab selected.");
      return;
    }

    let cancelled = false;

    (async () => {
      try {
        const d = await labsService.detail(lab.lab_id);
        if (cancelled) return;
        setDetail(d);

        // Start lab instance (or get existing)
        try {
          const inst = await labsService.start(lab.lab_id);
          if (!cancelled) setInstance(inst);
        } catch (e) {
          if (e.status === 409) {
            try {
              const inst = await labsService.status(lab.lab_id);
              if (!cancelled) setInstance(inst);
            } catch {}
          }
        }

        // Load sibling labs
        try {
          const sibs = await coursesService.labs(d.course_id);
          if (!cancelled) setSiblingLabs(sibs || []);
        } catch {}

        // ── Restore saved progress from DB ────────────────────────────────
        try {
          const prog = await labsService.myProgress(lab.lab_id);
          if (!cancelled && prog?.tasks) {
            const hintMeta   = {};
            const savedAnswers = {};
            const savedResults = {};

            for (const tp of prog.tasks) {
              const tid = tp.task_id;

              if (tp.hints_used > 0) {
                const taskHintCount = d.tasks?.find((t) => String(t.task_id) === String(tid))?.hint_count ?? 0;
                hintMeta[tid] = { total: taskHintCount, used: tp.hints_used };
              }

              if (tp.submitted_answer) {
                savedAnswers[tid] = tp.submitted_answer;
              }

              if (tp.is_correct === true) {
                savedResults[tid] = "correct";
              }
            }

            setHintMetaByTask(hintMeta);
            if (Object.keys(savedAnswers).length > 0) setAnswersByTask(savedAnswers);
            if (Object.keys(savedResults).length > 0) setResultsByTask(savedResults);
          }
        } catch {}

        // ── Restore global hint cooldown (one call for the whole lab) ────────
        try {
          const cooldownRes = await labsService.getLabHintCooldown(d.lab_id);
          if (!cancelled && cooldownRes.global_cooldown_ends_at && cooldownRes.seconds_remaining > 0) {
            const endsAt = new Date(cooldownRes.global_cooldown_ends_at).getTime();
            globalCooldownEndsAt.current = endsAt;
            setGlobalCountdown(Math.max(1, Math.ceil((endsAt - Date.now()) / 1000)));
            setHasGlobalCooldown(true);
          }
        } catch { /* non-fatal */ }

        // ── Restore revealed hint texts for each task ─────────────────────
        try {
          const tasksWithHints = d.tasks?.filter((t) => t.hint_count > 0) || [];
          if (tasksWithHints.length > 0) {
            const hintResults = await Promise.allSettled(
              tasksWithHints.map((t) => labsService.getRevealedHints(t.task_id))
            );
            if (!cancelled) {
              const hintsMap = {};
              const metaMap = {};
              for (let i = 0; i < tasksWithHints.length; i++) {
                const t = tasksWithHints[i];
                const result = hintResults[i];
                if (result.status !== "fulfilled") continue;
                const res = result.value;
                const tid = t.task_id;
                if (res.hints?.length > 0) hintsMap[tid] = res.hints;
                metaMap[tid] = { total: res.total_hints, used: res.hints_used };
              }
              if (Object.keys(hintsMap).length > 0)
                setHintsByTask((p) => ({ ...p, ...hintsMap }));
              if (Object.keys(metaMap).length > 0)
                setHintMetaByTask((p) => ({ ...p, ...metaMap }));
            }
          }
        } catch { /* non-fatal — hints still work, just no restore */ }

        // Restore persisted UI state (vmOpen, guacUrls) from localStorage
        const saved = loadLabState(lab.lab_id);
        if (saved && !cancelled) {
          if (saved.vmOpen) setVmOpen(true);
          if (saved.guacUrlA) setGuacUrlA(saved.guacUrlA);
          if (saved.guacUrlB) setGuacUrlB(saved.guacUrlB);
          if (saved.runtimeStatus) setRuntimeStatus(saved.runtimeStatus);
        }

        if (!cancelled) setLoadStatus("ready");
      } catch (e) {
        if (!cancelled) {
          // Auth failure → send back to login instead of showing a dead screen
          if (e.status === 401 || e.status === 403 ||
              /not authenticated|invalid token|unauthorized/i.test(e.message || "")) {
            nav("login");
            return;
          }
          setLoadError(e.message || "Failed to load lab");
          setLoadStatus("error");
        }
      }
    })();

    return () => { cancelled = true; };
  }, [lab?.lab_id, lab?.scenario_id, isScenarioLab]);

  // Persist vmOpen + guacUrls + revealed hint text to localStorage whenever they change
  useEffect(() => {
    if (lab?.lab_id && !isScenarioLab) {
      saveLabState(lab.lab_id, { vmOpen, guacUrlA, guacUrlB, runtimeStatus });
    }
  }, [vmOpen, guacUrlA, guacUrlB, runtimeStatus, hintsByTask, lab?.lab_id, isScenarioLab]);

  // Global hint countdown ticker — single timer shared across all tasks
  useEffect(() => {
    if (!hasGlobalCooldown) return;
    const id = setInterval(() => {
      const endsAt = globalCooldownEndsAt.current;
      if (!endsAt) { setHasGlobalCooldown(false); return; }
      const rem = Math.max(0, Math.ceil((endsAt - Date.now()) / 1000));
      setGlobalCountdown(rem);
      if (rem === 0) {
        globalCooldownEndsAt.current = null;
        setHasGlobalCooldown(false);
      }
    }, 500);
    return () => clearInterval(id);
  }, [hasGlobalCooldown]);

  // ── Auto-award certificate when all tasks become correct ─────────────────
  const allCorrectForEffect = detail ? (detail.tasks || []).every((t) => resultsByTask[t.task_id] === "correct") && (detail.tasks || []).length > 0 : false;
  useEffect(() => {
    if (loadStatus !== "ready") return;
    if (allCorrectInitRef.current === null) {
      // Seed the initial value without triggering anything
      allCorrectInitRef.current = allCorrectForEffect;
      return;
    }
    if (allCorrectForEffect && !allCorrectInitRef.current && detail?.course_id) {
      allCorrectInitRef.current = true;
      certificatesService.generate(detail.course_id)
        .then(() => setCertEarned(true))
        .catch(() => {});
    }
  }, [allCorrectForEffect, loadStatus]); // eslint-disable-line

  // Show badge celebration when lab is fully completed
  const celebrationFiredRef = useRef(false);
  useEffect(() => {
    if (allCorrectForEffect && !celebrationFiredRef.current && pendingBadges.length > 0) {
      celebrationFiredRef.current = true;
      setBadgeCelebration(pendingBadges);
    }
  }, [allCorrectForEffect, pendingBadges]);

  const tasks           = detail?.tasks || [];
  const totalTasks      = tasks.length;
  const completedTasks  = tasks.filter((t) => resultsByTask[t.task_id] === "correct").length;
  const progressPct     = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;
  const allCorrect      = totalTasks > 0 && completedTasks === totalTasks;
  const earnedPoints    = tasks.filter((t) => resultsByTask[t.task_id] === "correct")
                               .reduce((sum, t) => sum + (t.points || 0), 0);
  const totalPoints     = detail?.scoring?.max_points || tasks.reduce((s, t) => s + (t.points || 0), 0);

  const hintsRemaining = tasks.reduce((sum, t) => {
    const tid   = t.task_id;
    const total = hintMetaByTask[tid]?.total ?? t.hint_count ?? 0;
    if (total === 0) return sum;
    const used  = hintMetaByTask[tid]?.used ?? (hintsByTask[tid]?.length || 0);
    return sum + Math.max(0, total - used);
  }, 0);
  const allHintsRevealed = hintsRemaining === 0;
  const canAutoSolveLab = Boolean(detail?.has_auto_solve || tasks.some((t) => t.has_autosolve));
  const autosolveUnlocked = allHintsRevealed;
  const showTaskHints = isScenarioLab || runtimeSlug !== "metasploit";

  const nextLab = useMemo(() => {
    if (!detail || siblingLabs.length === 0) return null;
    const idx = siblingLabs.findIndex((l) => l.lab_id === detail.lab_id);
    if (idx < 0) return null;
    return siblingLabs[idx + 1] || null;
  }, [detail, siblingLabs]);

  const runtimeApi = useMemo(() => {
    const slug = detail?.runtime?.slug || detail?.docker_compose_config?.runtime_slug;
    return `${RUNTIME_BASE}/${slug || "ssh-bruteforce"}`;
  }, [detail]);

  const usesBackendRuntime = !isScenarioLab || Boolean(detail?.runtime?.slug || detail?.docker_compose_config?.runtime_slug);
  const showLaunch = !isScenarioLab || Boolean(detail?.runtime?.slug || detail?.docker_compose_config?.runtime_slug);
  const terminalStarting = vmOpen && usesBackendRuntime && (isDual ? (!guacUrlA || !guacUrlB) : !guacUrlA);

  const scrollTerminal = (direction) => {
    if (vmOpen) callRuntime(`/scroll?direction=${direction}`, "POST");
  };

  // ── Runtime calls ──────────────────────────────────────────────────────────
  const callRuntime = async (endpoint, method = "POST") => {
    setRuntimeMessage("Running...");
    try {
      const res = await fetch(`${runtimeApi}${endpoint}`, { method });
      if (!res.ok) {
        setRuntimeMessage(`Backend error ${res.status}. Restart the backend server.`);
        return null;
      }
      const data = await res.json();
      if (data.success) {
        setRuntimeMessage("Done.");
      } else {
        const detail = data.stderr || data.error || data.stdout || "";
        const short  = detail.split("\n").filter(Boolean).pop() || "Command failed — is Docker Desktop running?";
        setRuntimeMessage(short.slice(0, 220));
      }
      return data;
    } catch (e) {
      setRuntimeMessage(`Network error: ${e.message || "Cannot reach backend"}`);
      return null;
    }
  };

  const pollTerminalUrl = (endpoint, onUrl, label = "terminal") => {
    let attempts = 0;
    const maxAttempts = 20;
    const poll = async () => {
      try {
        const res  = await fetch(`${runtimeApi}${endpoint}`, { method: "GET" });
        const data = await res.json();
        if (data.success && data.url) {
          onUrl(data.url);
          setRuntimeMessage(`${label} ready.`);
        } else {
          attempts++;
          if (attempts < maxAttempts) {
            setRuntimeMessage(`Waiting for ${label}... (${attempts}/${maxAttempts})`);
            setTimeout(poll, 3000);
          } else {
            setRuntimeMessage(`${label} timed out. Try Reset Lab.`);
          }
        }
      } catch {
        attempts++;
        if (attempts < maxAttempts) setTimeout(poll, 3000);
        else setRuntimeMessage(`Could not reach ${label}. Is Docker running?`);
      }
    };
    setTimeout(poll, 5000);
  };

  const startRuntimeLab = async () => {
    if (isScenarioLab && !usesBackendRuntime) {
      setVmOpen(true);
      setRuntimeStatus("running");
      setRuntimeMessage("Scenario terminal ready.");
      return;
    }
    setVmOpen(true);
    setGuacUrlA(null);
    setGuacUrlB(null);
    setRuntimeMessage("Starting lab containers...");
    const data = await callRuntime("/start", "POST");
    if (data?.success) {
      setRuntimeStatus("running");
      if (isDual) {
        setRuntimeMessage("Connecting attacker terminal...");
        pollTerminalUrl("/terminal-url", setGuacUrlA, "Attacker terminal");
        pollTerminalUrl("/defender-url", setGuacUrlB, "Defender terminal");
      } else {
        setRuntimeMessage("Connecting terminal...");
        pollTerminalUrl("/terminal-url", setGuacUrlA, isDfKali ? "Forensics terminal" : "Terminal");
      }
      // Fetch live machine IPs for labs that expose a /machines endpoint
      if (runtimeSlug) {
        try {
          const mRes = await fetch(`${runtimeApi}/machines`);
          if (mRes.ok) {
            const mData = await mRes.json();
            if (mData.success) setMachineInfo(mData);
          }
        } catch { /* non-fatal */ }
      }
    }
  };

  const resetRuntimeLab = async () => {
    if (isScenarioLab && !usesBackendRuntime) {
      setRuntimeStatus("running");
      setRuntimeMessage("Progress reset.");
      setResultsByTask({});
      setHintsByTask({});
      setAnswersByTask({});
      setHintMetaByTask({});
      return;
    }
    const data = await callRuntime("/reset", "POST");
    if (data?.success) {
      setRuntimeStatus("running");
      setRuntimeMessage("Lab reset complete.");
      setGuacUrlA(null);
      setGuacUrlB(null);
      if (isDual) {
        pollTerminalUrl("/terminal-url", setGuacUrlA, "Attacker terminal");
        pollTerminalUrl("/defender-url", setGuacUrlB, "Defender terminal");
      } else {
        pollTerminalUrl("/terminal-url", setGuacUrlA, isDfKali ? "Forensics terminal" : "Terminal");
      }
    }
  };

  // ── Hint reveal ────────────────────────────────────────────────────────────
  const _applyGlobalCooldown = useCallback((global_cooldown_ends_at) => {
    if (!global_cooldown_ends_at) return;
    const endsAt = new Date(global_cooldown_ends_at).getTime();
    globalCooldownEndsAt.current = endsAt;
    const rem = Math.max(1, Math.ceil((endsAt - Date.now()) / 1000));
    setGlobalCountdown(rem);
    setHasGlobalCooldown(true);
  }, []);

  const revealHint = async (task) => {
    const tid = task.task_id;
    // Block if any global cooldown is active (shared across ALL tasks in this lab)
    if (hintBusyByTask[tid] || globalCountdown > 0) return;

    if (isScenarioLab) {
      const hints = task.local_hints || [];
      const used  = hintsByTask[tid]?.length || 0;
      const next  = hints[used];
      if (!next) return;
      setHintsByTask((p) => ({ ...p, [tid]: [...(p[tid] || []), { hint_id: `${tid}:h:${used}`, hint_text: next }] }));
      setHintMetaByTask((p) => ({ ...p, [tid]: { total: hints.length, used: used + 1 } }));
      // Apply client-side global cooldown and persist to localStorage
      const endsAt = Date.now() + 30_000;
      globalCooldownEndsAt.current = endsAt;
      setGlobalCountdown(30);
      setHasGlobalCooldown(true);
      try { localStorage.setItem(`hint-cooldown:${lab?.lab_id}`, String(endsAt)); } catch {}
      return;
    }

    setHintBusyByTask((p) => ({ ...p, [tid]: true }));
    try {
      const res = await labsService.requestHint(tid);
      setHintMetaByTask((p) => ({ ...p, [tid]: { total: res.total_hints, used: res.hints_used } }));

      if (res.is_available && res.hint) {
        setHintsByTask((p) => ({ ...p, [tid]: [...(p[tid] || []), res.hint] }));
      }
      // Always apply global cooldown from server — covers both success and rejection cases
      _applyGlobalCooldown(res.global_cooldown_ends_at);
    } catch (e) {
      setHintMetaByTask((p) => ({ ...p, [tid]: { ...(p[tid] || {}), error: e.message } }));
    } finally {
      setHintBusyByTask((p) => ({ ...p, [tid]: false }));
    }
  };

  // ── Answer submission ──────────────────────────────────────────────────────
  const submitAnswer = async (task) => {
    const tid    = task.task_id;
    const answer = (answersByTask[tid] || "").trim();
    if (!answer) return;

    if (isScenarioLab) {
      // Fuzzy match for scenario labs
      const expected = String(task.validation?.expected || "");
      const normalize = (s) => String(s || "").toLowerCase().replace(/[^a-z0-9\s]/g, " ").split(/\s+/).filter(Boolean);
      const aTokens   = normalize(answer);
      const eWords    = normalize(expected);
      const levenshtein = (a, b) => {
        if (a === b) return 0;
        const dp = Array.from({ length: a.length + 1 }, (_, i) => [i, ...Array(b.length).fill(0)]);
        for (let j = 0; j <= b.length; j++) dp[0][j] = j;
        for (let i = 1; i <= a.length; i++) for (let j = 1; j <= b.length; j++)
          dp[i][j] = Math.min(dp[i-1][j]+1, dp[i][j-1]+1, dp[i-1][j-1]+(a[i-1]===b[j-1]?0:1));
        return dp[a.length][b.length];
      };
      let matchCount = 0;
      for (const ew of eWords) {
        if (aTokens.some((at) => at.includes(ew) || ew.includes(at))) { matchCount++; continue; }
        if (aTokens.some((at) => levenshtein(at, ew) <= 1)) matchCount++;
      }
      const required  = Math.max(1, Math.ceil(eWords.length * 0.5));
      const isCorrect = matchCount >= required;
      setResultsByTask((p) => ({ ...p, [tid]: isCorrect ? "correct" : "incorrect" }));
      if (!isCorrect) setTimeout(() => setResultsByTask((p) => {
        if (p[tid] === "incorrect") { const { [tid]: _, ...rest } = p; return rest; } return p;
      }), 2500);
      return;
    }

    try {
      const res = await labsService.submitAnswer(tid, answer);
      setResultsByTask((p) => ({ ...p, [tid]: res.is_correct ? "correct" : "incorrect" }));
      if (!res.is_correct) {
        setTimeout(() => setResultsByTask((p) => {
          if (p[tid] === "incorrect") { const { [tid]: _, ...rest } = p; return rest; } return p;
        }), 2500);
      } else {
        if (onGamiRewards) onGamiRewards(res);
        if ((res.new_badges || []).length > 0) {
          setPendingBadges((p) => [...p, ...res.new_badges]);
        }
      }
    } catch {
      setResultsByTask((p) => ({ ...p, [tid]: "incorrect" }));
    }
  };

  // Typing animation: fills the answer box character by character
  const autofillAnswer = useCallback((taskId, answer) => {
    if (!answer) return;
    const chars = [...answer];
    if (chars.length === 0) return;
    // Speed: 30–40 ms/char, capped at 2 s total
    const delayMs = Math.min(40, 2000 / chars.length);
    if (typingTimeoutsRef.current[taskId]) clearTimeout(typingTimeoutsRef.current[taskId]);
    setAutofillingTasks((p) => { const n = new Set(p); n.add(taskId); return n; });
    let i = 0;
    const tick = () => {
      i++;
      setAnswersByTask((p) => ({ ...p, [taskId]: chars.slice(0, i).join("") }));
      if (i < chars.length) {
        typingTimeoutsRef.current[taskId] = setTimeout(tick, delayMs);
      } else {
        delete typingTimeoutsRef.current[taskId];
        setAutofillingTasks((p) => { const n = new Set(p); n.delete(taskId); return n; });
      }
    };
    typingTimeoutsRef.current[taskId] = setTimeout(tick, delayMs);
  }, []);

  // ── Lab-level autosolve (single button at bottom) ─────────────────────────
  const runLabAutosolve = useCallback(async () => {
    if (!detail?.lab_id) return;
    if (!autosolveUnlocked) return;

    if (isScenarioLab) {
      setAutosolveCurrentTask(null);
      setLabAutosolve({ busy: true, done: false, error: "" });

      if (!vmOpen) {
        setVmOpen(true);
        setRuntimeMessage("Starting VM for auto-solve...");
        await callRuntime("/start", "POST");
      }

      const data = await callRuntime("/autosolve", "POST");
      if (!data?.success) {
        setLabAutosolve({ busy: false, done: false, error: "Auto-solve failed. Check Docker Desktop and try again." });
        return;
      }

      for (const task of tasks) {
        const answer = task.validation?.expected || "";
        setAutosolveCurrentTask(task.task_id);
        if (answer) autofillAnswer(task.task_id, answer);
        setResultsByTask((p) => ({ ...p, [task.task_id]: "correct" }));
      }

      setAutosolveCurrentTask(null);
      setLabAutosolve({ busy: false, done: true, error: "" });
      setRuntimeStatus("running");
      setRuntimeMessage("Auto-solve complete.");
      return;
    }

    const token = localStorage.getItem(TOKEN_KEY) || "";
    if (!token) {
      setLabAutosolve({ busy: false, done: false, error: "Not logged in — please refresh." });
      return;
    }

    setAutosolveCurrentTask(null);
    setLabAutosolve({ busy: true, done: false, error: "" });

    // Make sure the VM panel is open so the student can watch
    if (!vmOpen) {
      setVmOpen(true);
      setRuntimeMessage("Starting VM for auto-solve...");
      await callRuntime("/start", "POST");
    }

    const ws = labsService.openLabAutosolveWS(detail.lab_id, token, (msg) => {
      switch (msg.type) {
        case "status":
          // VM startup / operational messages — show in the runtime bar
          setRuntimeMessage(msg.message || "");
          break;

        case "start":
          setAutosolveCurrentTask(null);
          break;

        case "task_start":
          setAutosolveCurrentTask(msg.task_id);
          break;

        case "output":
          break;

        case "task_done":
          if (msg.task_id) {
            setResultsByTask((p) => ({ ...p, [msg.task_id]: "correct" }));
            if (msg.answer) autofillAnswer(msg.task_id, msg.answer);
            setAutosolveCurrentTask(null);
            if ((msg.new_badges || []).length > 0) {
              setPendingBadges((p) => [...p, ...msg.new_badges]);
            }
            if (onGamiRewards && (msg.xp_gained || msg.level_up || (msg.new_badges || []).length > 0)) {
              onGamiRewards(msg);
            }
          }
          break;

        case "done":
          setLabAutosolve((p) => ({ ...p, busy: false, done: true }));
          setAutosolveCurrentTask(null);
          break;

        case "error":
          setLabAutosolve((p) => ({ ...p, busy: false, error: msg.data }));
          setAutosolveCurrentTask(null);
          break;

        default:
          break;
      }
    });

    ws.onopen  = () => setRuntimeMessage("Auto-solve connected — executing commands...");
    ws.onclose = (e) => {
      setLabAutosolve((p) => {
        if (!p.busy) return p;
        const reason = e.reason || (e.code === 4001 ? "Unauthorized" : "Connection lost.");
        return { ...p, busy: false, error: `Auto-solve failed: ${reason}` };
      });
      setAutosolveCurrentTask(null);
    };
  }, [vmOpen, detail?.lab_id, isScenarioLab, autosolveUnlocked, tasks, autofillAnswer]);

  // ── Submit / exit lab ─────────────────────────────────────────────────────
  const submitLab = async () => {
    if (!allCorrect) return;
    if (!isScenarioLab) { try { await labsService.stop(lab.lab_id); } catch {} }
    if (nextLab) {
      nav("lab", { lab: { ...nextLab, courseTitle: lab.courseTitle, courseCategory: lab.courseCategory, labIndex: (lab.labIndex ?? 0) + 1, totalLabs: lab.totalLabs } });
    } else {
      nav("course-detail", { course: { course_id: isScenarioLab ? "fake-4" : detail.course_id, title: lab.courseTitle, category: lab.courseCategory, difficulty_level: "intermediate", estimated_hours: 18 } });
    }
  };

  const exitLab = async () => {
    if (!isScenarioLab) { try { if (instance) await labsService.stop(lab.lab_id); } catch {} }
    nav("course-detail", { course: { course_id: isScenarioLab ? "fake-4" : detail?.course_id, title: lab?.courseTitle, category: lab?.courseCategory, difficulty_level: "intermediate", estimated_hours: 18 } });
  };

  if (loadStatus === "loading") return <div className="app"><div className="ls"><CyberLoader text="Deploying lab..." /></div></div>;
  if (loadStatus === "error")   return <div className="app"><div className="ls"><div style={{ textAlign: "center", color: "var(--text-muted)" }}><p>{loadError}</p><button className="btn ba2" style={{ marginTop: 16 }} onClick={() => nav("courses")}>Back to courses</button></div></div></div>;

  const envMeta = ENV_META[envReq] || ENV_META.none;

  return (
    <div className="lab2">
      <div className="lab2-top">
        <div className="lab2-top-row">
          <div className="lab2-top-left">
            <button className="ib" onClick={exitLab} title="Exit lab"><I.Left /></button>
            <div>
              <div className="lab2-top-title">{detail.title}</div>
              <div className="lab2-top-sub">
                {lab.courseTitle}
                {lab.labIndex != null && lab.totalLabs != null && (
                  <span> · Lab {lab.labIndex + 1} of {lab.totalLabs}</span>
                )}
              </div>
            </div>
          </div>
          <div className="lab2-top-right">
            <div className="lab2-progress-text">
              <span className="lab2-progress-num">{completedTasks}/{totalTasks}</span>
              <span className="lab2-progress-label">{earnedPoints}/{totalPoints} pts</span>
            </div>
            <button className="tt" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
              {theme === "dark" ? <I.Sun /> : <I.Moon />}
            </button>
          </div>
        </div>
        <div className="lab2-progress-bar">
          <div className="lab2-progress-fill" style={{ width: `${progressPct}%` }} />
        </div>
      </div>

      <div className="lab2-body" style={vmOpen ? {} : { gridTemplateColumns: "1fr" }}>
        <div className="lab2-tasks">

          {certEarned && (
            <div className="lab-cert-banner">
              <div className="lab-cert-banner-left">
                <I.Award />
                <div>
                  <div className="lab-cert-banner-title">Certificate Earned!</div>
                  <div className="lab-cert-banner-sub">You've completed the course. Your certificate is ready.</div>
                </div>
              </div>
              <button className="btn bg bs" style={{ fontSize: 12 }} onClick={() => nav("certificates")}>
                View Certificate <I.Right />
              </button>
            </div>
          )}

          {detail.description && (
            <div className="lab-intro-card">
              <div className="lab-intro-label"><I.Book /> Lab Overview</div>
              <p className="lab-intro-text">{detail.description}</p>
            </div>
          )}

          {isScenarioLab && detail.objectives?.length > 0 && (
            <div className="lab-intro-card">
              <div className="lab-intro-label"><I.Flag /> Objectives</div>
              <div className="task-card-instructions">{detail.objectives.map((o) => <p key={o}>{o}</p>)}</div>
            </div>
          )}

          <div className="lab-env-banner" style={{ borderColor: envMeta.color }}>
            <span className="lab-env-icon">{envMeta.icon}</span>
            <div className="lab-env-body">
              <span className="lab-env-label" style={{ color: envMeta.color }}>{envMeta.label}</span>
              <span className="lab-env-desc">{envMeta.desc}</span>
            </div>
            {isDual && (
              <div className="lab-env-roles">
                <span className="lab-env-role attacker">⚔ Attacker</span>
                <span className="lab-env-role defender">🛡 Defender</span>
              </div>
            )}
          </div>

          {totalTasks === 0 && <div className="empty-state"><p>This lab has no tasks yet.</p></div>}

          {tasks.map((t, i) => (
            <TaskCard
              key={t.task_id}
              index={i}
              task={t}
              answer={answersByTask[t.task_id] || ""}
              setAnswer={(v) => setAnswersByTask((p) => ({ ...p, [t.task_id]: v }))}
              onSubmit={() => submitAnswer(t)}
              result={resultsByTask[t.task_id]}
              hints={hintsByTask[t.task_id] || []}
              meta={hintMetaByTask[t.task_id]}
              countdown={globalCountdown}
              hintBusy={hintBusyByTask[t.task_id]}
              onRevealHint={() => revealHint(t)}
              isScenarioLab={isScenarioLab}
              showHints={showTaskHints}
              autofilling={autofillingTasks.has(t.task_id)}
            />
          ))}

          {!vmOpen && showLaunch && (
            <div className="lab-launch-cta">
              <button className="lab-launch-btn" onClick={startRuntimeLab}>
                <I.Monitor />
                {isDual ? "Launch Terminals (Attack + Defense)" : isDfKali ? "Launch Forensics Kali" : "Launch Machine"}
              </button>
              <p className="lab-launch-hint">
                {isDual ? "Opens attacker Kali + defender target terminals side by side"
                : isDfKali ? "Opens a Kali Linux container with forensics tools (Docker)"
                : "Opens a live terminal alongside your tasks"}
              </p>
            </div>
          )}

          {/* ── Lab-level Auto Solve button ───────────────────────────────── */}
          {canAutoSolveLab && (
            <div className="lab-autosolve-section">
              <button
                className={`lab-autosolve-btn${labAutosolve.busy ? " busy" : ""}${labAutosolve.done ? " done" : ""}${!autosolveUnlocked ? " locked" : ""}`}
                onClick={runLabAutosolve}
                disabled={labAutosolve.busy || !autosolveUnlocked}
                title={!autosolveUnlocked ? "Open all hints first" : ""}
              >
                <I.Zap />
                {labAutosolve.busy
                  ? "Executing…"
                  : labAutosolve.done
                  ? "Auto-Solve Complete ✓"
                  : "Auto Solve Lab"}
              </button>
              <p className="lab-autosolve-hint">
                {labAutosolve.busy
                  ? "Commands are running inside the VM — watch the terminal."
                  : labAutosolve.done
                  ? "All tasks solved. Answers have been filled in automatically."
                  : !autosolveUnlocked
                  ? "You must open all hints before using Auto Solve."
                  : "Executes all lab commands inside the VM, captures output, and fills your answers."}
              </p>
              {labAutosolve.error && (
                <div className="ae" style={{ marginTop: 8 }}>{labAutosolve.error}</div>
              )}
            </div>
          )}

          {totalTasks > 0 && (
            <div className="lab2-finalize">
              <button
                className={`submit-lab-btn ${allCorrect ? "ready" : ""}`}
                disabled={!allCorrect}
                onClick={submitLab}
              >
                {allCorrect
                  ? nextLab ? <span>Next: {nextLab.title}</span> : "Submit Lab"
                  : `Complete all tasks first (${completedTasks}/${totalTasks})`}
              </button>
            </div>
          )}
        </div>

        {/* ── VM / Terminal panel ───────────────────────────────────────────── */}
        {vmOpen && (
          <div className="lab2-vm">
            <div className="lab2-vm-bar">
              <div className="lab2-vm-status">
                <span className={`vm-dot ${runtimeStatus === "running" ? "live" : ""}`} />
                <span>
                  {isDfKali
                    ? runtimeStatus === "running" ? "Forensics Kali Connected" : "Forensics Kali Stopped"
                    : isDual
                    ? runtimeStatus === "running" ? "Dual Terminal Connected" : "Dual Terminal Stopped"
                    : runtimeStatus === "running" ? "Kali Runtime Connected" : "Kali Runtime Stopped"}
                </span>
              </div>
              <div className="vm-timer-group">
                <span className={`vm-timer${sessionSecs < 600 ? " warn" : ""}`}>
                  {sessionSecs === 0 ? "Expired" : formatCountdown(sessionSecs)}
                </span>
                <button className="vm-timer-extend" onClick={() => setSessionSecs((s) => s + 1800)} title="Add 30 minutes">+30 min</button>
              </div>
              <button className="ib" onClick={() => setVmOpen(false)} title="Collapse terminal"><I.X /></button>
            </div>

            <div style={{ padding: "16px", height: "100%", overflow: "hidden", display: "flex", flexDirection: "column" }}>
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "10px" }}>
                <button className="btn ba2" onClick={resetRuntimeLab}>Reset Lab</button>
              </div>

              {runtimeStatus === "running" && usesBackendRuntime && (
                isDual ? (
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", marginBottom: "10px" }}>
                    <MachineInfoCard label="Attacker (Kali)"    ip={detail.runtime?.attacker?.ip   || "172.25.0.20"} user={detail.runtime?.attacker?.user   || "attacker"} password={detail.runtime?.attacker?.password   || "attacker123"} dotColor="#ff5f56" />
                    <MachineInfoCard label="Defender (Target)"  ip={detail.runtime?.defender?.ip  || "172.25.0.10"} user={detail.runtime?.defender?.user  || "defender"}  password={detail.runtime?.defender?.password  || "defender123"}  dotColor="#27c93f" />
                  </div>
                ) : isDfKali ? (
                  <MachineInfoCard label="Forensics Kali (df-kali)" ip={detail.runtime?.target_ip || "172.30.0.10"} user={detail.runtime?.user || "student"} password={detail.runtime?.password || "kali"} dotColor="#a78bfa" style={{ marginBottom: "10px" }} />
                ) : machineInfo ? (
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", marginBottom: "10px" }}>
                    <MachineInfoCard label={machineInfo.attacker.label} ip={machineInfo.attacker.ip} user={machineInfo.attacker.user} password={machineInfo.attacker.password} dotColor="#ff5f56" />
                    <MachineInfoCard label={machineInfo.target.label} ip={machineInfo.target.ip} user="msfadmin" password="msfadmin" extra={`hostname: ${machineInfo.target.hostname}`} dotColor="#27c93f" />
                  </div>
                ) : (
                  <div style={{ fontSize: "11px", color: "var(--text-muted)", marginBottom: "8px" }}>
                    Loading machine info…
                  </div>
                )
              )}

              {runtimeMessage && (
                <div style={{ background: "#050505", color: "#00ff66", border: "1px solid rgba(0,255,102,0.25)", borderRadius: "10px", padding: "8px 10px", height: "34px", overflow: "hidden", whiteSpace: "nowrap", textOverflow: "ellipsis", fontSize: "11px", marginBottom: "8px", fontFamily: "monospace" }} title={runtimeMessage}>
                  {runtimeMessage}
                </div>
              )}

              {/* Terminal area */}
              {isScenarioLab && !usesBackendRuntime ? (
                <div className="lab2-vm-screen" style={{ flex: 1 }}>
                  <div className="lab2-vm-prompt">
                    <p>CyberArcade scenario terminal ready.</p>
                    <p><span className="cr">_</span></p>
                  </div>
                </div>
              ) : isDual ? (
                <div style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0 }}>
                  <div className="dual-term-tabs">
                    <button className={`dual-term-tab attacker${activeTermTab === "A" ? " active" : ""}`} onClick={() => setActiveTermTab("A")}>
                      ⚔ Attacker (Kali){guacUrlA && <span className="term-tab-dot live" />}
                    </button>
                    <button className={`dual-term-tab defender${activeTermTab === "B" ? " active" : ""}`} onClick={() => setActiveTermTab("B")}>
                      🛡 Defender (Target){guacUrlB && <span className="term-tab-dot live" />}
                    </button>
                  </div>
                  {/* Keep both iframes alive using visibility instead of display:none */}
                  <div style={{ flex: 1, minHeight: 0, position: "relative" }}>
                    <div style={{ position: "absolute", inset: 0, visibility: activeTermTab === "A" ? "visible" : "hidden", pointerEvents: activeTermTab === "A" ? "auto" : "none" }}>
                      <LabTerminal guacUrl={guacUrlA} role="attacker" active={activeTermTab === "A"} starting={terminalStarting && !guacUrlA} onScrollUp={() => scrollTerminal("up")} onScrollDown={() => scrollTerminal("down")} onScrollExit={() => scrollTerminal("exit")} />
                    </div>
                    <div style={{ position: "absolute", inset: 0, visibility: activeTermTab === "B" ? "visible" : "hidden", pointerEvents: activeTermTab === "B" ? "auto" : "none" }}>
                      <LabTerminal guacUrl={guacUrlB} role="defender" active={activeTermTab === "B"} starting={terminalStarting && !guacUrlB} onScrollUp={() => scrollTerminal("up")} onScrollDown={() => scrollTerminal("down")} onScrollExit={() => scrollTerminal("exit")} />
                    </div>
                  </div>
                </div>
              ) : (
                <div style={{ flex: 1, minHeight: 0 }}>
                  <LabTerminal guacUrl={guacUrlA} role={isDfKali ? "df-kali" : "single"} active={true} starting={terminalStarting && !guacUrlA} onScrollUp={() => scrollTerminal("up")} onScrollDown={() => scrollTerminal("down")} onScrollExit={() => scrollTerminal("exit")} />
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <button className="ai-fab" onClick={() => setChatOpen(!chatOpen)} title="AI Assistant">
        {chatOpen ? <I.X /> : <I.Bot />}
      </button>
      {chatOpen && <div className="ai-popup"><Chat onClose={() => setChatOpen(false)} labId={lab?.lab_id} /></div>}

      {/* Badge celebration overlay */}
      {badgeCelebration && (
        <div className="badge-cel-overlay" onClick={() => setBadgeCelebration(null)}>
          <div className="badge-cel-box" onClick={(e) => e.stopPropagation()}>
            <div className="badge-cel-glow" />
            <div className="badge-cel-title">
              {badgeCelebration.length === 1 ? "Badge Unlocked!" : `${badgeCelebration.length} Badges Unlocked!`}
            </div>
            <div className="badge-cel-list">
              {badgeCelebration.map((b, i) => (
                <div key={i} className="badge-cel-card">
                  <div className="badge-cel-icon">{b.icon || "🏅"}</div>
                  <div className="badge-cel-info">
                    <div className="badge-cel-name">{b.name}</div>
                    <div className="badge-cel-desc">{b.description}</div>
                    {b.xp_reward > 0 && (
                      <div className="badge-cel-xp">+{b.xp_reward} XP</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
            <button className="badge-cel-btn" onClick={() => setBadgeCelebration(null)}>
              Awesome!
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Machine info card ─────────────────────────────────────────────────────────
function MachineInfoCard({ label, ip, user, password, dotColor, extra, style }) {
  return (
    <div style={{ background: "rgba(0,0,0,0.3)", border: `1px solid ${dotColor}33`, borderRadius: "10px", padding: "10px 14px", fontFamily: "monospace", fontSize: "12px", ...style }}>
      <div style={{ color: dotColor, fontWeight: "bold", marginBottom: "6px", fontSize: "10px", textTransform: "uppercase", letterSpacing: "0.06em" }}>
        <span style={{ display: "inline-block", width: 8, height: 8, borderRadius: "50%", background: dotColor, marginRight: 6 }} />{label}
      </div>
      <div style={{ color: "#888" }}>IP: <span style={{ color: dotColor }}>{ip}</span></div>
      {extra && <div style={{ color: "#888" }}>{extra}</div>}
      {user && <div style={{ color: "#888" }}>User: <span style={{ color: dotColor }}>{user}</span></div>}
      {password && <div style={{ color: "#888" }}>Pass: <span style={{ color: dotColor }}>{password}</span></div>}
    </div>
  );
}

// ── Task card ─────────────────────────────────────────────────────────────────
function TaskCard({ index, task, answer, setAnswer, onSubmit, result, hints, meta, countdown, hintBusy, onRevealHint, isScenarioLab, showHints = true, solving, autofilling }) {
  const totalHints = meta?.total ?? task.hint_count ?? 0;
  const hintsUsed  = meta?.used  ?? hints.length;

  const cardClass = [
    "task-card",
    result === "correct" ? "task-done" : "",
    solving ? "task-solving" : "",
  ].filter(Boolean).join(" ");

  return (
    <div className={cardClass}>
      <div className="task-card-head">
        <div className="task-card-num">{String(index + 1).padStart(2, "0")}</div>
        <div className="task-card-titles">
          <h3>{task.title}</h3>
          <div className="task-card-instructions task-md">
            <ReactMarkdown>{task.instructions || ""}</ReactMarkdown>
          </div>
        </div>
        {solving && <div className="task-solving-badge">Executing…</div>}
      </div>

      <div className={`task-answer-wrap ${result || ""}`}>
        <input
          className={`task-answer-input${autofilling ? " autofilling" : ""}`}
          placeholder="Enter your answer..."
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && result !== "correct" && onSubmit()}
          disabled={result === "correct"}
        />
        <div className="task-answer-tail">
          {result === "correct"  && <span className="answer-ok"><I.Check /></span>}
          {result === "incorrect" && <span className="answer-no"><I.X /></span>}
          {!result && (
            <button className="task-answer-submit" onClick={onSubmit} disabled={!answer.trim()}>
              <I.Right />
            </button>
          )}
        </div>
      </div>

      {showHints && (
        <TaskHints
          hints={hints}
          totalHints={totalHints}
          hintsUsed={hintsUsed}
          countdown={countdown}
          hintBusy={hintBusy}
          locked={false}
          onRevealHint={onRevealHint}
          meta={meta}
        />
      )}
    </div>
  );
}
