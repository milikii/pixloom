"use client";

import { RefreshCw, Trash2 } from "lucide-react";
import type { TaskRecord, TaskSummary } from "@/lib/types";
import { zh } from "@/i18n/zh";
import { TaskDetail } from "./TaskDetail";
import { StatusBadge } from "./StatusBadge";

function formatTime(iso: string) {
  return iso.slice(11, 16);
}

export function TaskSummaryView({ summary }: { summary: TaskSummary }) {
  return (
    <div className="mb-4 space-y-1 font-mono text-[13px] text-muted-foreground">
      <p>
        共 <span className="font-semibold text-foreground">{summary.total}</span>{" "}
        个任务 —{" "}
        排队 {summary.queued} · 运行 {summary.running} · 完成 {summary.completed}{" "}
        · 失败 {summary.failed}
      </p>
      {summary.cleanup_text && (
        <p className="text-xs">{summary.cleanup_text}</p>
      )}
    </div>
  );
}

export function TaskListView({
  tasks,
  selectedId,
  onSelect,
}: {
  tasks: TaskRecord[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  if (tasks.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-muted-foreground">
        {zh.empty.noTasks}
      </p>
    );
  }

  return (
    <div className="max-h-80 space-y-0.5 overflow-y-auto">
      {tasks.map((t) => (
        <button
          key={t.request_id}
          onClick={() => onSelect(t.request_id)}
          className={`w-full rounded-lg px-3 py-2 text-left font-mono text-xs leading-relaxed transition-colors ${
            selectedId === t.request_id
              ? "bg-accent-subtle ring-1 ring-accent/20"
              : "hover:bg-muted/50"
          }`}
        >
          <div className="flex items-center gap-2">
            <StatusBadge status={t.status} />
            <span className="text-muted-foreground">
              {formatTime(t.created_at)}
            </span>
            <span className="truncate text-muted-foreground">
              {t.input_filename}
            </span>
          </div>
          <div className="ml-5 mt-0.5 text-muted-foreground">
            {t.progress_step || "—"}{" "}
            {t.elapsed_seconds !== null ? `| ${t.elapsed_seconds.toFixed(1)}s` : ""}
            {t.error_code ? ` | ${t.error_code}` : ""}
          </div>
        </button>
      ))}
    </div>
  );
}

interface TaskPanelProps {
  tasks: TaskRecord[];
  summary: TaskSummary;
  selectedTask: TaskRecord | null;
  selectedId: string | null;
  onSelect: (id: string) => void;
  onRefresh: () => void;
  onDelete: () => void;
  deletePending: boolean;
  disabled?: boolean;
}

export function TaskPanel({
  tasks,
  summary,
  selectedTask,
  selectedId,
  onSelect,
  onRefresh,
  onDelete,
  deletePending,
  disabled,
}: TaskPanelProps) {
  return (
    <div className="space-y-4">
      <TaskSummaryView summary={summary} />

      <div>
        <label className="mb-1.5 block text-xs font-medium text-muted-foreground">
          选择任务
        </label>
        <TaskListView
          tasks={tasks}
          selectedId={selectedId}
          onSelect={onSelect}
        />
      </div>

      {selectedTask && (
        <div>
          <h3 className="mb-2 text-sm font-medium text-foreground">
            {zh.detail.taskDetail}
          </h3>
          <TaskDetail task={selectedTask} />
        </div>
      )}

      <div className="flex gap-2">
        <button
          onClick={onRefresh}
          disabled={disabled}
          className="inline-flex items-center gap-2 rounded-lg border border-border px-4 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:border-accent hover:bg-accent-subtle hover:text-accent disabled:pointer-events-none disabled:opacity-40"
        >
          <RefreshCw className="h-4 w-4" />
          {zh.refresh.label}
        </button>
        <button
          onClick={onDelete}
          disabled={!selectedId || disabled || deletePending}
          className="inline-flex items-center gap-2 rounded-lg border border-destructive-subtle px-4 py-2.5 text-sm font-medium text-destructive transition-colors hover:bg-destructive-subtle hover:border-destructive disabled:pointer-events-none disabled:opacity-40"
        >
          {deletePending ? (
            <RefreshCw className="h-4 w-4 animate-spin" />
          ) : (
            <Trash2 className="h-4 w-4" />
          )}
          {zh.delete.label}
        </button>
      </div>
    </div>
  );
}
