"use client";

import { useState, type ReactNode } from "react";
import { zh } from "@/i18n/zh";

interface Tab {
  key: string;
  label: string;
  content: ReactNode;
}

interface ResultsTabsProps {
  tabs: Tab[];
  defaultTab?: string;
}

export function ResultsTabs({ tabs, defaultTab }: ResultsTabsProps) {
  const [active, setActive] = useState(defaultTab ?? tabs[0]?.key ?? "");
  const current = tabs.find((t) => t.key === active);

  return (
    <div>
      <div className="flex overflow-x-auto border-b border-border">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActive(tab.key)}
            className={`relative shrink-0 px-5 py-3 text-sm font-medium transition-colors duration-150 ${
              active === tab.key
                ? "text-foreground"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab.label}
            {active === tab.key && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent" />
            )}
          </button>
        ))}
      </div>
      <div className="pt-4">{current?.content}</div>
    </div>
  );
}
