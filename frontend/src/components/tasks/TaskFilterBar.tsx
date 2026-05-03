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

const TIME_OPTIONS: { key: string; label: string; days: number | null }[] = [
  { key: "today", label: "今天", days: 0 },
  { key: "3days", label: "最近 3 天", days: 3 },
  { key: "7days", label: "最近 7 天", days: 7 },
  { key: "all", label: "全部", days: null },
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

/** Filter tasks by status and time window. */
export function applyFilters<T extends { status: string; created_at: string }>(
  tasks: T[],
  statusFilter: TaskStatus | "all",
  timeFilter: string,
): T[] {
  const TIME_WINDOWS: Record<string, number | null> = {
    today: 0,
    "3days": 3,
    "7days": 7,
    all: null,
  };
  const days = TIME_WINDOWS[timeFilter] ?? null;

  return tasks.filter((t) => {
    if (statusFilter !== "all" && t.status !== statusFilter) return false;
    if (days !== null) {
      const cutoff = new Date();
      cutoff.setDate(cutoff.getDate() - days);
      cutoff.setHours(0, 0, 0, 0);
      if (new Date(t.created_at) < cutoff) return false;
    }
    return true;
  });
}
