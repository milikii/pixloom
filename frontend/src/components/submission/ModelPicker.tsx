"use client";

import { ChevronDown } from "lucide-react";
import type { ResolvedModel } from "@/lib/types";

interface ModelPickerProps {
  models: ResolvedModel[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  disabled?: boolean;
}

const SPEED_BADGES: Record<string, string> = {
  "很慢": "🐢",
  "普通偏慢": "",
  "普通": "",
  "较快": "⚡",
};

export function ModelPicker({
  models,
  selectedId,
  onSelect,
  disabled,
}: ModelPickerProps) {
  return (
    <div className="relative mb-5">
      <select
        value={selectedId ?? ""}
        onChange={(e) => onSelect(e.target.value)}
        disabled={disabled || models.length === 0}
        className="w-full appearance-none rounded-lg border border-border-strong bg-surface px-4 py-3 pr-10 text-sm text-foreground transition-colors focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20 disabled:opacity-50"
      >
        {models.length === 0 && (
          <option value="">无可用模型</option>
        )}
        {models.map((m) => (
          <option key={m.id} value={m.id}>
            {m.display_name_zh || m.display_name}
            {SPEED_BADGES[m.speed_zh]
              ? `  ${SPEED_BADGES[m.speed_zh]}`
              : ""}
          </option>
        ))}
      </select>
      <ChevronDown className="pointer-events-none absolute right-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
    </div>
  );
}
