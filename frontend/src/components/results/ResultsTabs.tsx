"use client";

import { useState, type ReactNode } from "react";

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
      {/* Mobile: capsule pills. Desktop: underline tabs. */}
      <div className="flex overflow-x-auto gap-1.5 md:gap-0 md:border-b md:border-border">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActive(tab.key)}
            className={`relative shrink-0 text-sm font-medium transition-colors duration-150
              md:rounded-none md:px-5 md:py-3
              rounded-full px-4 py-2
              ${
                active === tab.key
                  ? "bg-accent text-white md:bg-transparent md:text-foreground"
                  : "text-muted-foreground hover:text-foreground md:hover:bg-transparent"
              }`}
          >
            {tab.label}
            {active === tab.key && (
              <span className="hidden md:block absolute bottom-0 left-0 right-0 h-0.5 bg-accent" />
            )}
          </button>
        ))}
      </div>
      <div className="pt-4">{current?.content}</div>
    </div>
  );
}
