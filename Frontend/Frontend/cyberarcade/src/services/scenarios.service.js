const scenarioModules = import.meta.glob("../scenarios/*.json", {
  eager: true,
  import: "default",
});

const difficultyMap = {
  easy: "beginner",
  beginner: "beginner",
  medium: "intermediate",
  intermediate: "intermediate",
  hard: "advanced",
  advanced: "advanced",
};

const normalizeDifficulty = (difficulty = "beginner") => {
  const key = String(difficulty).toLowerCase();
  return difficultyMap[key] || key;
};

const scenarios = Object.values(scenarioModules).sort((a, b) =>
  (a.order || 999) - (b.order || 999) || a.title.localeCompare(b.title)
);

// Only used as a last-resort fallback for scenarios with no runtime field at all.
// Scenarios should explicitly set runtime: null (no terminal) or runtime: { slug, terminal_type, ... }.
const DEFAULT_RUNTIME = {
  slug: "ssh-bruteforce",
  terminal: "guacamole",
  terminal_type: "single",
  target_ip: "172.25.0.10",
};

const runtimeFor = (scenario) => {
  if (Object.prototype.hasOwnProperty.call(scenario, "runtime") && scenario.runtime === null) return null;
  return scenario.runtime || DEFAULT_RUNTIME;
};

// ── Environment requirement descriptor ────────────────────────────────────────
// Returns what environment a lab needs so the UI can show a badge.
// Possible values: "none" | "terminal" | "dual" | "df-kali"
export const envRequirement = (runtime) => {
  if (!runtime) return "none";
  const type = runtime.terminal_type;
  if (type === "dual") return "dual";
  if (type === "df-kali") return "df-kali";
  return "terminal";
};

const toLab = (scenario) => {
  const runtime = runtimeFor(scenario);
  return {
    lab_id: `scenario:${scenario.id}`,
    scenario_id: scenario.id,
    title: scenario.title,
    description: scenario.story,
    difficulty: normalizeDifficulty(scenario.difficulty),
    duration: scenario.duration,
    category: scenario.category,
    points: scenario.scoring?.max_points || scenario.tasks.reduce((sum, task) => sum + task.points, 0),
    has_auto_solve: Boolean(scenario.autosolve?.enabled),
    runtime,
    env_requirement: envRequirement(runtime),
    isScenario: true,
  };
};

const toDetail = (scenario) => {
  const runtime = runtimeFor(scenario);
  return {
    lab_id: `scenario:${scenario.id}`,
    scenario_id: scenario.id,
    title: scenario.title,
    description: scenario.story,
    course_id: `${scenario.category.toLowerCase().replace(/\s+/g, '-')}-scenarios`,
    category: scenario.category,
    difficulty: normalizeDifficulty(scenario.difficulty),
    duration: scenario.duration,
    objectives: scenario.objectives || [],
    scoring: scenario.scoring || {},
    runtime,
    terminal_type: runtime?.terminal_type || null,
    docker_compose_config: runtime ? { runtime_slug: runtime.slug } : {},
    has_auto_solve: Boolean(scenario.autosolve?.enabled),
    autosolve_script: scenario.autosolve?.script || "autosolve.sh",
    env_requirement: envRequirement(runtime),
    tasks: (scenario.tasks || []).map((task) => {
      const hints = Array.isArray(task.hints)
        ? task.hints
        : task.hint
        ? [task.hint]
        : [];

      return {
        task_id: `scenario:${scenario.id}:${task.id}`,
        local_id: task.id,
        title: task.title,
        instructions: task.description,
        description: task.description,
        points: task.points || 0,
        hint_count: hints.length,
        local_hints: hints,
        validation: task.validation,
        has_autosolve: Boolean(scenario.autosolve?.enabled),
      };
    }),
  };
};

export const scenariosService = {
  list() {
    return scenarios;
  },

  labsByCategory(category) {
    return scenarios
      .filter((scenario) => scenario.category === category)
      .map(toLab);
  },

  detail(id) {
    const scenarioId = String(id || "").replace(/^scenario:/, "");
    const scenario = scenarios.find((item) => item.id === scenarioId);
    if (!scenario) throw new Error("Scenario not found.");
    return toDetail(scenario);
  },

  toLab,
  envRequirement,
};
