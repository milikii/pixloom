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

const TIME_OPTIONS: { key: string; label: string; match: (localDate: string) => boolean }[] = [
  { key: "today", label: "今天", match: (d) => d === todayStr() },
  { key: "yesterday", label: "昨天", match: (d) => d === yesterdayStr() },
  { key: "3days", label: "最近 3 天", match: (d) => d >= daysAgoStr(3) },
  { key: "7days", label: "最近 7 天", match: (d) => d >= daysAgoStr(7) },
  { key: "thisMonth", label: "本月", match: (d) => d >= thisMonthStartStr() },
  { key: "all", label: "全部", match: () => true },
];

function localDateStr(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`;
}
function todayStr(): string { return localDateStr(new Date()); }
function yesterdayStr(): string { const d = new Date(); d.setDate(d.getDate()-1); return localDateStr(d); }
function daysAgoStr(n: number): string { const d = new Date(); d.setDate(d.getDate()-n); return localDateStr(d); }
function thisMonthStartStr(): string { return localDateStr(new Date(new Date().getFullYear(), new Date().getMonth(), 1)); }

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
      <div className="flex flex-wrap gap-1.5">
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

/** Extract YYYY-MM-DD from an ISO timestamp string. */
function isoDateStr(iso: string): string {
  return iso.slice(0, 10);
}

/** Filter tasks by status and time window. Deleted tasks are always excluded. */
export function applyFilters<T extends { status: string; created_at: string }>(
  tasks: T[],
  statusFilter: TaskStatus | "all",
  timeFilter: string,
): T[] {
  const option = TIME_OPTIONS.find((o) => o.key === timeFilter);
  const match = option?.match ?? (() => true);

  return tasks.filter((t) => {
    if (t.status === "deleted") return false;
    if (statusFilter !== "all" && t.status !== statusFilter) return false;
    if (!match(isoDateStr(t.created_at))) return false;
    return true;
  });
}
