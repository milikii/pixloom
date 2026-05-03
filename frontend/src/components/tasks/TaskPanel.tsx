"use client";

import { useState } from "react";
import {
  RefreshCw,
  Trash2,
  Download,
  ChevronDown,
  ChevronRight,
  Image,
  FileText,
} from "lucide-react";
import type { TaskRecord, TaskSummary } from "@/lib/types";
import { zh } from "@/i18n/zh";
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

function fileUrl(outputPath: string | null) {
  if (!outputPath) return null;
  const name = outputPath.replace(/^.*[\\/]/, "");
  return `/api/files/output/${encodeURIComponent(name)}`;
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
  logExcerpt: string | null;
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
  logExcerpt,
}: TaskPanelProps) {
  const [detailOpen, setDetailOpen] = useState(false);
  const completedTasks = tasks.filter(
    (t) => t.status === "completed" && t.output_path
  );
  const previewUrl = selectedTask ? fileUrl(selectedTask.output_path) : null;

  return (
    <div className="space-y-4">
      {/* Header bar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3 text-sm">
          <span className="font-medium text-foreground">
            任务列表
          </span>
          <span className="font-mono text-muted-foreground">
            {summary.total} 个 | 完成 {summary.completed} | 失败 {summary.failed}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {completedTasks.length > 0 && (
            <BatchDownloadButton tasks={completedTasks} />
          )}
          <button
            onClick={onRefresh}
            disabled={disabled}
            className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-2 text-xs font-medium text-muted-foreground transition-colors hover:border-accent hover:bg-accent-subtle hover:text-accent disabled:pointer-events-none disabled:opacity-40"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            刷新
          </button>
        </div>
      </div>

      {/* Task list */}
      <div className="max-h-[360px] space-y-1 overflow-y-auto">
        {tasks.length === 0 ? (
          <p className="py-10 text-center text-sm text-muted-foreground">
            {zh.empty.noTasks}
          </p>
        ) : (
          tasks.map((t) => {
            const thumb = fileUrl(t.output_path);
            const isSelected = selectedId === t.request_id;

            return (
              <button
                key={t.request_id}
                onClick={() => onSelect(t.request_id)}
                className={`flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left transition-colors ${
                  isSelected
                    ? "bg-accent-subtle ring-1 ring-accent/20"
                    : "hover:bg-muted/50"
                }`}
              >
                {/* Thumbnail — larger for completed */}
                {thumb && t.status === "completed" ? (
                  <div className="relative h-14 w-14 shrink-0 overflow-hidden rounded-md border border-border bg-muted">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={thumb}
                      alt=""
                      className="h-full w-full object-cover"
                    />
                  </div>
                ) : t.status === "running" ? (
                  <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-md border border-info/20 bg-info-subtle">
                    <div className="h-5 w-5 animate-spin rounded-full border-2 border-info/30 border-t-info" />
                  </div>
                ) : (
                  <div className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-md border ${
                    t.status === "failed"
                      ? "border-destructive/20 bg-destructive-subtle"
                      : "border-border bg-muted/30"
                  }`}>
                    {/* eslint-disable-next-line jsx-a11y/alt-text */}
                    <Image className={`h-5 w-5 ${
                      t.status === "failed" ? "text-destructive/50" : "text-muted-foreground/30"
                    }`} />
                  </div>
                )}

                {/* Info — compact single line */}
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <StatusBadge status={t.status} />
                    <span className="font-mono text-[11px] text-muted-foreground">
                      {formatTime(t.created_at)}
                    </span>
                    {t.status === "running" && (
                      <span className="font-mono text-[11px] text-info">
                        {Math.round(t.progress_value * 100)}%
                      </span>
                    )}
                    {t.elapsed_seconds && (
                      <span className="font-mono text-[11px] text-muted-foreground">
                        {formatElapsed(t.elapsed_seconds)}
                      </span>
                    )}
                  </div>
                  <div className="mt-0.5 truncate text-[12px] text-foreground">
                    {t.input_filename}
                  </div>
                  {t.status === "failed" && t.error_code && (
                    <div className="mt-0.5 font-mono text-[11px] text-destructive/70">
                      {t.error_code}
                    </div>
                  )}
                </div>

                {/* Select indicator */}
                {isSelected && (
                  <div className="mr-1 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                )}
              </button>
            );
          })
        )}
      </div>

      {/* Inline result preview — shown when a completed task is selected */}
      {selectedTask && selectedTask.status === "completed" && previewUrl && (
        <div className="rounded-xl border border-border bg-muted/10 overflow-hidden">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={previewUrl}
            alt={`${selectedTask.input_filename} 放大结果`}
            className="w-full"
          />
          <div className="flex items-center gap-3 border-t border-border px-4 py-3">
            <span className="flex-1 truncate font-mono text-xs text-muted-foreground">
              {selectedTask.output_path?.replace(/^.*[\\/]/, "")}
            </span>
            <a
              href={previewUrl}
              download
              className="inline-flex items-center gap-1.5 rounded-lg bg-accent px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-accent-hover"
            >
              <Download className="h-3.5 w-3.5" />
              下载此结果
            </a>
          </div>
        </div>
      )}

      {/* Running task status */}
      {selectedTask && selectedTask.status === "running" && (
        <div className="rounded-xl border border-info/20 bg-info-subtle px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-info/30 border-t-info" />
            <div className="flex-1">
              <div className="text-sm font-medium text-foreground">
                {selectedTask.progress_step || "处理中..."}
              </div>
              <div className="mt-1 h-1.5 rounded-full bg-muted overflow-hidden">
                <span
                  className="block h-full rounded-full bg-info transition-all duration-500"
                  style={{ width: `${Math.round(selectedTask.progress_value * 100)}%` }}
                />
              </div>
            </div>
            <span className="font-mono text-sm text-info">
              {Math.round(selectedTask.progress_value * 100)}%
            </span>
          </div>
        </div>
      )}

      {/* Failed task info */}
      {selectedTask && selectedTask.status === "failed" && (
        <div className="rounded-xl border border-destructive-subtle bg-destructive-subtle px-4 py-3">
          <p className="text-sm font-medium text-destructive">
            {selectedTask.error_code}
          </p>
          <p className="mt-0.5 text-xs text-destructive/70">
            {selectedTask.error_detail || "未知错误"}
          </p>
        </div>
      )}

      {/* Task detail — collapsible */}
      {selectedTask && (
        <div className="overflow-hidden rounded-xl border border-border">
          <button
            onClick={() => setDetailOpen(!detailOpen)}
            className="flex w-full items-center justify-between px-4 py-2.5 text-left text-xs font-medium text-muted-foreground transition-colors hover:bg-muted/30"
          >
            {detailOpen ? "收起详情" : "展开详情"}
            {detailOpen ? (
              <ChevronDown className="h-3.5 w-3.5" />
            ) : (
              <ChevronRight className="h-3.5 w-3.5" />
            )}
          </button>
          {detailOpen && (
            <div className="border-t border-border px-4 py-3 font-mono text-[12px] leading-relaxed">
              <div className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1">
                <span className="text-muted-foreground">请求 ID</span>
                <span className="select-all text-foreground">{selectedTask.request_id}</span>
                <span className="text-muted-foreground">批次 ID</span>
                <span className="select-all text-foreground">{selectedTask.batch_id}</span>
                <span className="text-muted-foreground">模型</span>
                <span className="text-foreground">{selectedTask.model_id}</span>
                <span className="text-muted-foreground">耗时</span>
                <span className="text-foreground">{formatElapsed(selectedTask.elapsed_seconds) || "—"}</span>
                <span className="text-muted-foreground">创建</span>
                <span className="text-foreground">{selectedTask.created_at}</span>
                {selectedTask.completed_at && (
                  <>
                    <span className="text-muted-foreground">完成</span>
                    <span className="text-foreground">{selectedTask.completed_at}</span>
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Delete button */}
      <button
        onClick={onDelete}
        disabled={!selectedId || disabled || deletePending}
        className="inline-flex w-full items-center justify-center gap-2 rounded-lg border border-destructive-subtle px-4 py-2.5 text-sm font-medium text-destructive transition-colors hover:bg-destructive-subtle hover:border-destructive disabled:pointer-events-none disabled:opacity-40"
      >
        {deletePending ? (
          <RefreshCw className="h-4 w-4 animate-spin" />
        ) : (
          <Trash2 className="h-4 w-4" />
        )}
        {zh.delete.label}
      </button>

      {/* Log excerpt */}
      {logExcerpt && (
        <div className="rounded-xl border border-border bg-muted/30 p-4">
          <div className="mb-2 flex items-center gap-2 text-xs text-muted-foreground">
            <FileText className="h-3.5 w-3.5" />
            请求日志
          </div>
          <pre className="whitespace-pre-wrap break-all font-mono text-xs leading-relaxed text-foreground">
            {logExcerpt}
          </pre>
        </div>
      )}
    </div>
  );
}

function BatchDownloadButton({ tasks }: { tasks: TaskRecord[] }) {
  function handleBatchDownload() {
    tasks.forEach((t) => {
      const url = fileUrl(t.output_path);
      if (url) {
        // Open each in a new tab for download
        const a = document.createElement("a");
        a.href = url;
        a.download = "";
        a.click();
      }
    });
  }

  return (
    <button
      onClick={handleBatchDownload}
      className="inline-flex items-center gap-1.5 rounded-lg border border-success/30 bg-success-subtle px-3 py-2 text-xs font-medium text-success transition-colors hover:bg-success/10 hover:border-success/50"
    >
      <Download className="h-3.5 w-3.5" />
      批量下载已完成 ({tasks.length})
    </button>
  );
}
