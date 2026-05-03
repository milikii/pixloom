"use client";

import { RefreshCw, Trash2, Image } from "lucide-react";
import type { TaskRecord, TaskSummary } from "@/lib/types";
import { zh } from "@/i18n/zh";
import { TaskDetail } from "./TaskDetail";
import { StatusBadge } from "./StatusBadge";

function formatTime(iso: string) {
  return iso.slice(11, 16);
}

function formatElapsed(seconds: number | null) {
  if (seconds === null || seconds === undefined) return "";
  if (seconds < 60) return `${seconds.toFixed(0)}s`;
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m}m${s}s`;
}

function thumbnailUrl(outputPath: string | null) {
  if (!outputPath) return null;
  const name = outputPath.replace(/^.*[\\/]/, "");
  return `/api/files/output/${encodeURIComponent(name)}`;
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
    <div className="max-h-80 space-y-1 overflow-y-auto">
      {tasks.map((t) => {
        const thumb = thumbnailUrl(t.output_path);
        const isSelected = selectedId === t.request_id;

        return (
          <button
            key={t.request_id}
            onClick={() => onSelect(t.request_id)}
            className={`w-full rounded-lg px-3 py-2 text-left transition-colors ${
              isSelected
                ? "bg-accent-subtle ring-1 ring-accent/20"
                : "hover:bg-muted/50"
            }`}
          >
            <div className="flex items-center gap-3">
              {/* Thumbnail or placeholder */}
              {thumb && t.status === "completed" ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={thumb}
                  alt={t.input_filename}
                  className="h-10 w-10 shrink-0 rounded-md border border-border object-cover"
                />
              ) : t.status === "running" ? (
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-info/20 bg-info-subtle">
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-info/30 border-t-info" />
                </div>
              ) : t.status === "failed" ? (
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-destructive/20 bg-destructive-subtle">
                  {/* eslint-disable-next-line jsx-a11y/alt-text */}
                  <Image className="h-4 w-4 text-destructive/50" />
                </div>
              ) : (
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-border bg-muted/30">
                  {/* eslint-disable-next-line jsx-a11y/alt-text */}
                  <Image className="h-4 w-4 text-muted-foreground/40" />
                </div>
              )}

              {/* Info */}
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <StatusBadge status={t.status} />
                  <span className="text-[11px] text-muted-foreground">
                    {formatTime(t.created_at)}
                  </span>
                </div>
                <div className="mt-0.5 flex items-center gap-2 font-mono text-[12px] text-foreground">
                  <span className="truncate">{t.input_filename}</span>
                </div>
                <div className="mt-0.5 flex items-center gap-2 text-[11px] text-muted-foreground">
                  {t.status === "running" && (
                    <>
                      <span>{Math.round(t.progress_value * 100)}%</span>
                      <span className="w-16 h-1 rounded-full bg-muted overflow-hidden">
                        <span
                          className="block h-full rounded-full bg-info transition-all duration-500"
                          style={{ width: `${Math.round(t.progress_value * 100)}%` }}
                        />
                      </span>
                      {t.elapsed_seconds && (
                        <span>{formatElapsed(t.elapsed_seconds)}</span>
                      )}
                    </>
                  )}
                  {t.status === "completed" && t.elapsed_seconds && (
                    <span>{formatElapsed(t.elapsed_seconds)}</span>
                  )}
                  {t.status === "failed" && t.error_code && (
                    <span className="text-destructive/80">{t.error_code}</span>
                  )}
                  {t.progress_step && t.status !== "running" && (
                    <span className="hidden sm:inline">{t.progress_step}</span>
                  )}
                </div>
              </div>
            </div>
          </button>
        );
      })}
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
