// helpers.js — shared utility functions

/**
 * Clamp a number between min and max
 */
export function clamp(val, min, max) {
  return Math.min(Math.max(val, min), max);
}

/**
 * Format a number as a percentage string
 * e.g. formatPercent(0.75) → "75%"
 */
export function formatPercent(ratio) {
  return `${Math.round(ratio * 100)}%`;
}

/**
 * Slugify a string for use in URLs or keys
 * e.g. slugify("Network Recon") → "network-recon"
 */
export function slugify(str) {
  return str.toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "");
}

/**
 * Capitalize the first letter of a string
 */
export function capitalize(str) {
  if (!str) return "";
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Delay execution for ms milliseconds
 */
export function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Return a difficulty CSS class name
 * e.g. difficultyClass("Beginner") → "d-beginner"
 */
export function difficultyClass(difficulty = "") {
  return `d-${difficulty.toLowerCase()}`;
}

/**
 * Format estimated hours (backend returns a float like 2.5) into a short
 * human-readable string. Falls back to "—" when null/undefined.
 */
export function formatHours(hours) {
  if (hours == null) return "—";
  const n = Number(hours);
  if (!isFinite(n)) return "—";
  if (Number.isInteger(n)) return `${n}h`;
  return `${n.toFixed(1)}h`;
}

/**
 * Format a seconds countdown as m:ss. Used by the lab hint timer.
 */
export function formatCountdown(seconds) {
  const s = Math.max(0, Math.floor(seconds));
  const m = Math.floor(s / 60);
  const rem = s % 60;
  if (m === 0) return `${rem}s`;
  return `${m}:${rem.toString().padStart(2, "0")}`;
}