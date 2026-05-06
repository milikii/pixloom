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

function optionLabel(model: ResolvedModel) {
  const speedBadge = SPEED_BADGES[model.speed_zh]
    ? `  ${SPEED_BADGES[model.speed_zh]}`
    : "";
  return `${model.display_name_zh || model.display_name}${speedBadge}`;
}

export function ModelPicker({
  models,
  selectedId,
  onSelect,
  disabled,
}: ModelPickerProps) {
  const selectedModel = models.find((model) => model.id === selectedId) ?? null;
  const groupedModels = models.reduce<Map<string, ResolvedModel[]>>((groups, model) => {
    const key = model.group_label_zh || "未分类";
    const current = groups.get(key) ?? [];
    current.push(model);
    groups.set(key, current);
    return groups;
  }, new Map());

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
        {[...groupedModels.entries()].map(([groupLabel, groupModels]) => (
          <optgroup key={groupLabel} label={groupLabel}>
            {groupModels.map((model) => (
              <option key={model.id} value={model.id}>
                {optionLabel(model)}
              </option>
            ))}
          </optgroup>
        ))}
      </select>
      <ChevronDown className="pointer-events-none absolute right-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
      {groupedModels.size > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {[...groupedModels.entries()].map(([groupLabel, groupModels]) => {
            const isActive = selectedModel?.group_label_zh === groupLabel;
            return (
              <span
                key={groupLabel}
                className={`inline-flex min-h-8 items-center rounded-full px-3 py-1 text-[11px] font-medium transition-colors ${
                  isActive
                    ? "bg-accent-subtle text-accent ring-1 ring-accent/20"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                {groupLabel}
                <span className="ml-1 opacity-70">{groupModels.length}</span>
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
}
