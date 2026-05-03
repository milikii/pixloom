"use client";

import { useTheme } from "next-themes";
import { Sun, Moon } from "lucide-react";
import { useEffect, useState } from "react";

interface ThemeToggleProps {
  variant?: "default" | "header";
}

export function ThemeToggle({ variant = "default" }: ThemeToggleProps) {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // next-themes mount guard to avoid hydration mismatch
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => setMounted(true), []);

  if (!mounted) {
    return <div className="h-9 w-9" />;
  }

  const isHeader = variant === "header";

  return (
    <button
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
      className={`flex h-9 w-9 items-center justify-center rounded-lg border transition-colors ${
        isHeader
          ? "border-white/10 hover:border-white/25 hover:bg-white/[0.08]"
          : "border-border hover:bg-accent-subtle hover:border-accent"
      }`}
      aria-label={theme === "dark" ? "切换到亮色模式" : "切换到深夜模式"}
    >
      {theme === "dark" ? (
        <Sun className={`h-4 w-4 ${isHeader ? "text-header-text" : "text-warning"}`} />
      ) : (
        <Moon className={`h-4 w-4 ${isHeader ? "text-header-text" : "text-accent"}`} />
      )}
    </button>
  );
}
