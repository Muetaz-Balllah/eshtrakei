"use client";

import { useEffect, useState } from "react";
import { Icon } from "@/components/ui/ui";
import { ar } from "@/messages/ar";

export function ThemeToggle({ compact = false }: { compact?: boolean }) {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    setDark(document.documentElement.classList.contains("dark"));
  }, []);

  function toggle() {
    const next = !document.documentElement.classList.contains("dark");
    document.documentElement.classList.toggle("dark", next);
    localStorage.setItem("theme", next ? "dark" : "light");
    setDark(next);
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={dark ? ar.lightMode : ar.darkMode}
      className={`inline-flex items-center justify-center gap-2 font-bold text-secondary transition hover:bg-surface-container ${
        compact ? "h-11 w-11 rounded-full" : "min-h-11 rounded-2xl bg-surface-low px-3 text-sm"
      }`}
    >
      <Icon name={dark ? "light_mode" : "dark_mode"} className="text-[22px]" />
      {compact ? null : <span>{dark ? ar.lightMode : ar.darkMode}</span>}
    </button>
  );
}
