"use client";

import {
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Info,
} from "lucide-react";
import { useState } from "react";
import type { ResolvedModel } from "@/lib/types";
import { zh } from "@/i18n/zh";

interface ModelGuidanceProps {
  model: ResolvedModel | null;
  hiddenCount: number;
  hasLocalModels: boolean;
  hasSelectedModel: boolean;
}

export function ModelGuidance({
  model,
  hiddenCount,
  hasLocalModels,
  hasSelectedModel,
}: ModelGuidanceProps) {
  const [open, setOpen] = useState(true);

  function starLabel(count: number) {
    const safe = Math.max(0, Math.min(5, count));
    return `${"★".repeat(safe)}${"☆".repeat(5 - safe)}`;
  }

  function renderContent() {
    if (!model && hasLocalModels) {
      return (
        <div className="flex items-start gap-3">
          <Info className="mt-0.5 h-5 w-5 shrink-0 text-warning" />
          <div>
            <p className="text-sm text-foreground">{zh.model.noOperatorReady}</p>
            {hiddenCount > 0 && (
              <p className="mt-2 text-xs text-muted-foreground">
                {zh.model.hiddenNote.replace("{count}", String(hiddenCount))}
              </p>
            )}
          </div>
        </div>
      );
    }
    if (!model) {
      return (
        <div className="flex items-start gap-3">
          <Info className="mt-0.5 h-5 w-5 shrink-0 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">{zh.model.noModels}</p>
        </div>
      );
    }
    if (!hasSelectedModel) {
      return (
        <p className="text-sm text-muted-foreground">{zh.model.select}</p>
      );
    }

    const stabilityIcon =
      model.stability_zh === "已首轮实测" || model.stability_zh.includes("已本机") ? (
        <CheckCircle2 className="h-4 w-4 text-success" />
      ) : model.stability_zh === "未启用" ? (
        <Clock className="h-4 w-4 text-muted-foreground" />
      ) : (
        <AlertTriangle className="h-4 w-4 text-warning" />
      );

    return (
      <div>
        <h3 className="mb-3 text-sm font-semibold text-foreground">
          {model.display_name_zh || model.display_name}
        </h3>
        <p className="mb-3 text-xs text-muted-foreground">
          {model.group_label_zh || "未分类"}
        </p>
        <ul className="space-y-2 text-sm">
          <li className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">优先级</span>
            <span className="text-foreground">{starLabel(model.priority_stars)}</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="mt-0.5 shrink-0 text-xs text-muted-foreground">
              适合
            </span>
            <span className="text-foreground">
              {model.recommended_for_zh || "请参考模型名称选择。"}
            </span>
          </li>
          <li className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">风格</span>
            <span className="text-foreground">{model.style_zh || "未标注"}</span>
          </li>
          <li className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">速度</span>
            <span className="text-foreground">{model.speed_zh || "未标注"}</span>
          </li>
          <li className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">状态</span>
            <span className="inline-flex items-center gap-1.5 text-foreground">
              {stabilityIcon}
              {model.stability_zh || "未标注"}
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="mt-0.5 shrink-0 text-xs text-muted-foreground">
              提醒
            </span>
            <span className="text-muted-foreground">
              {model.warning_zh || "当前没有额外提醒。"}
            </span>
          </li>
          {model.sharp_review_zh && (
            <li className="flex items-start gap-2">
              <span className="mt-0.5 shrink-0 text-xs text-warning">锐评</span>
              <span className="text-foreground leading-relaxed">
                {model.sharp_review_zh}
              </span>
            </li>
          )}
        </ul>
        {hiddenCount > 0 && (
          <p className="mt-3 border-t border-border pt-3 text-xs text-muted-foreground">
            {zh.model.hiddenNote.replace("{count}", String(hiddenCount))}
          </p>
        )}
      </div>
    );
  }

  return (
    <div className="mb-5 overflow-hidden rounded-xl border border-border bg-surface">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-foreground transition-colors hover:bg-muted/50"
      >
        模型与策略
        {open ? (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-4 w-4 text-muted-foreground" />
        )}
      </button>
      {open && <div className="border-t border-border px-4 pb-4 pt-3">{renderContent()}</div>}
    </div>
  );
}
