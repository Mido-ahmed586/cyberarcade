import { useState, useEffect } from "react";
import themes from "../data/themes";

export function useTheme() {
  // Default to light mode
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem("ca-theme") || "light";
  });

  useEffect(() => {
    const root = document.documentElement;
    root.setAttribute("data-theme", theme);
    Object.entries(themes[theme]).forEach(([k, v]) => root.style.setProperty(k, v));
    localStorage.setItem("ca-theme", theme);
  }, [theme]);

  const toggleTheme = () => setTheme((t) => (t === "dark" ? "light" : "dark"));

  return { theme, setTheme, toggleTheme };
}