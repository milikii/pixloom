"use client";

import type { TaskStatus } from "@/lib/types";

const STATUS_OPTIONS: { key: TaskStatus | "all"; label: string }[] = [
  { key: "all", label: "全部" },
  { key: "queued", label: "排队中" },
  { key: "running", label: "处理中" },
  { key: "completed", label: "已完成" },
  { key: "failed", label: "失败" },
  { key: "interrupted", label: "已中断" },
];

const TIME_OPTIONS: { key: string; label: string; getCutoff: () => Date | null }[] = [
  { key: "today", label: "今天", getCutoff: () => { const d = new Date(); d.setHours(0,0,0,0); return d; } },
  { key: "yesterday", label: "昨天", getCutoff: () => { const d = new Date(); d.setDate(d.getDate()-1); d.setHours(0,0,0,0); return d; } },
  { key: "3days", label: "最近 3 天", getCutoff: () => { const d = new Date(); d.setDate(d.getDate()-3); d.setHours(0,0,0,0); return d; } },
  { key: "7days", label: "最近 7 天", getCutoff: () => { const d = new Date(); d.setDate(d.getDate()-7); d.setHours(0,0,0,0); return d; } },
  { key: "thisMonth", label: "本月", getCutoff: () => { const d = new Date(); d.setDate(1); d.setHours(0,0,0,0); return d; } },
  { key: "all", label: "全部", getCutoff: () => null },
];

interface TaskFilterBarProps {
  statusFilter: TaskStatus | "all";
  onStatusChange: (status: TaskStatus | "all") => void;
  timeFilter: string;
  onTimeChange: (key: string) => void;
  statusCounts: Record<string, number>;
}

export function TaskFilterBar({
  statusFilter,
  onStatusChange,
  timeFilter,
  onTimeChange,
  statusCounts,
}: TaskFilterBarProps) {
  return (
    <div className="space-y-2">
      {/* Status filter pills */}
      <div className="flex flex-wrap gap-1.5">
        {STATUS_OPTIONS.map((opt) => (
          <button
            key={opt.key}
            onClick={() => onStatusChange(opt.key)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              statusFilter === opt.key
                ? "bg-accent text-white"
                : "bg-muted text-muted-foreground hover:bg-muted-foreground/15"
            }`}
          >
            {opt.label}
            {statusCounts[opt.key] !== undefined && (
              <span className="ml-1 opacity-70">{statusCounts[opt.key]}</span>
            )}
          </button>
        ))}
      </div>

      {/* Time filter */}
      <div className="flex gap-1.5">
        {TIME_OPTIONS.map((opt) => (
          <button
            key={opt.key}
            onClick={() => onTimeChange(opt.key)}
            className={`rounded-full px-2.5 py-0.5 text-[11px] font-medium transition-colors ${
              timeFilter === opt.key
                ? "bg-accent-subtle text-accent ring-1 ring-accent/20"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}

/** Filter tasks by status and time window. Deleted tasks are always excluded. */
export function applyFilters<T extends { status: string; created_at: string }>(
  tasks: T[],
  statusFilter: TaskStatus | "all",
  timeFilter: string,
): T[] {
  const option = TIME_OPTIONS.find((o) => o.key === timeFilter);
  const cutoff = option?.getCutoff() ?? null;

  return tasks.filter((t) => {
    if (t.status === "deleted") return false;
    if (statusFilter !== "all" && t.status !== statusFilter) return false;
    if (cutoff !== null && new Date(t.created_at) < cutoff) return false;
    return true;
  });
}
