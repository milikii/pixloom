"use client";

import { useMemo, useState } from "react";
import {
  RefreshCw,
  Trash2,
  ChevronDown,
  ChevronRight,
  Image as ImageIcon,
  Download,
} from "lucide-react";
import type { TaskRecord, TaskStatus } from "@/lib/types";
import { zh } from "@/i18n/zh";
import { apiClient } from "@/lib/api-client";
import { RequestLogs } from "@/components/logs/RequestLogs";
import { StatusBadge } from "./StatusBadge";
import { TaskFilterBar, applyFilters } from "./TaskFilterBar";
import { BatchActionBar } from "./BatchActionBar";

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

function thumbnailUrl(outputPath: string | null, size = 160) {
  if (!outputPath) return null;
  const name = outputPath.replace(/^.*[\\/]/, "");
  return `/api/files/output-thumbnail/${encodeURIComponent(name)}?size=${size}`;
}

function triggerUrlDownload(url: string) {
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
}

interface TaskPanelProps {
  tasks: TaskRecord[];
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
  selectedTask,
  selectedId,
  onSelect,
  onRefresh,
  onDelete,
  deletePending,
  disabled,
  logExcerpt,
}: TaskPanelProps) {
  const [statusFilter, setStatusFilter] = useState<TaskStatus | "all">("all");
  const [timeFilter, setTimeFilter] = useState("all");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [detailOpen, setDetailOpen] = useState(false);
  const [downloadPending, setDownloadPending] = useState(false);

  const filteredTasks = useMemo(
    () => applyFilters(tasks, statusFilter, timeFilter),
    [tasks, statusFilter, timeFilter],
  );

  const statusCounts = useMemo(() => {
    const now = new Date();
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    return {
      all: tasks.length,
      queued: tasks.filter((t) => t.status === "queued").length,
      running: tasks.filter((t) => t.status === "running").length,
      completed: tasks.filter((t) => t.status === "completed").length,
      failed: tasks.filter((t) => t.status === "failed").length,
      interrupted: tasks.filter((t) => t.status === "interrupted").length,
      today: tasks.filter((t) => new Date(t.created_at) >= todayStart).length,
    };
  }, [tasks]);

  // Only completed tasks with output are selectable for batch download
  const selectableTasks = filteredTasks.filter(
    (t) => t.status === "completed" && t.output_path,
  );
  const allSelectableSelected =
    selectableTasks.length > 0 &&
    selectableTasks.every((t) => selectedIds.has(t.request_id));

  const handleToggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleBatchDownload = () => {
    const requestIds = selectableTasks
      .filter((t) => selectedIds.has(t.request_id))
      .map((t) => t.request_id);
    if (requestIds.length === 0) return;

    setDownloadPending(true);
    triggerUrlDownload(apiClient.taskArchiveUrl(requestIds));
    window.setTimeout(() => setDownloadPending(false), 1500);
  };

  const handleSelectAll = () => {
    setSelectedIds(new Set(selectableTasks.map((t) => t.request_id)));
  };

  const handleClearSelection = () => setSelectedIds(new Set());

  const handleSelect = (id: string) => {
    onSelect(id);
    setDetailOpen(true);
  };

  const previewUrl = selectedTask ? fileUrl(selectedTask.output_path) : null;
  const selectedBatchTasks = selectedTask
    ? tasks.filter((t) => t.batch_id === selectedTask.batch_id && t.status !== "deleted")
    : [];
  const selectedBatchCompleted = selectedBatchTasks.filter(
    (t) => t.status === "completed",
  ).length;
  const selectedBatchFailed = selectedBatchTasks.filter(
    (t) => t.status === "failed" || t.status === "interrupted",
  ).length;
  const partialBatchText =
    selectedBatchTasks.length > 1 &&
    selectedBatchCompleted > 0 &&
    selectedBatchFailed > 0
      ? `当前批次部分完成：${selectedBatchCompleted} 个成功，${selectedBatchFailed} 个失败或中断。失败项已保留在任务列表和日志里。`
      : "";

  const resultContent =
    selectedTask && selectedTask.status === "completed" && previewUrl ? (
      <div className="overflow-hidden rounded-xl border border-border bg-muted/10">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={previewUrl}
          alt={`${selectedTask.input_filename} 放大结果`}
          decoding="async"
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
    ) : (
      <div className="flex min-h-44 flex-col items-center justify-center rounded-xl border border-border bg-muted/20 px-4 py-10 text-center">
        <ImageIcon className="h-7 w-7 text-muted-foreground/40" />
        <p className="mt-3 text-sm text-muted-foreground">
          {selectedTask
            ? selectedTask.progress_summary || "当前任务还没有可预览结果。"
            : zh.empty.noTaskSelected}
        </p>
      </div>
    );

  const taskListContent = (
    <div className="space-y-3">
      <TaskFilterBar
        statusFilter={statusFilter}
        onStatusChange={(s) => {
          setStatusFilter(s);
          setSelectedIds(new Set());
        }}
        timeFilter={timeFilter}
        onTimeChange={(t) => {
          setTimeFilter(t);
          setSelectedIds(new Set());
        }}
        statusCounts={statusCounts}
      />

      <BatchActionBar
        selectedIds={selectedIds}
        selectableCount={selectableTasks.length}
        allSelected={allSelectableSelected}
        downloadPending={downloadPending}
        onSelectAll={handleSelectAll}
        onDownload={handleBatchDownload}
        onClear={handleClearSelection}
      />

      <div className="max-h-[360px] space-y-1 overflow-y-auto">
        {filteredTasks.length === 0 ? (
          <p className="py-10 text-center text-sm text-muted-foreground">
            {tasks.length === 0 ? zh.empty.noTasks : "没有匹配的任务"}
          </p>
        ) : (
          filteredTasks.map((t) => {
            const thumb = thumbnailUrl(t.output_path);
            const isSelected = selectedId === t.request_id;
            const isChecked = selectedIds.has(t.request_id);
            const isSelectable = t.status === "completed" && !!t.output_path;

            return (
              <div
                key={t.request_id}
                className={`flex items-center gap-2 rounded-lg transition-colors ${
                  isSelected
                    ? "bg-accent-subtle ring-1 ring-accent/20"
                    : "hover:bg-muted/50"
                }`}
              >
                {isSelectable ? (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleToggleSelect(t.request_id);
                    }}
                    className={`ml-2 flex h-4 w-4 shrink-0 items-center justify-center rounded border-2 transition-colors ${
                      isChecked
                        ? "border-accent bg-accent text-white"
                        : "border-border-strong hover:border-accent/50"
                    }`}
                    aria-label={`选择 ${t.input_filename}`}
                  >
                    {isChecked && (
                      <svg className="h-3 w-3" viewBox="0 0 12 12" fill="none">
                        <path
                          d="M2.5 6L5 8.5L9.5 3.5"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                    )}
                  </button>
                ) : (
                  <div className="ml-2 w-4 shrink-0" />
                )}

                <button
                  onClick={() => handleSelect(t.request_id)}
                  className="flex min-w-0 flex-1 items-center gap-2 py-1.5 pr-2 text-left"
                >
                  {thumb && t.status === "completed" ? (
                    <div className="relative h-14 w-14 shrink-0 overflow-hidden rounded-md border border-border bg-muted">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={thumb}
                        alt=""
                        decoding="async"
                        className="h-full w-full object-cover"
                      />
                    </div>
                  ) : t.status === "running" ? (
                    <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-md border border-info/20 bg-info-subtle">
                      <div className="h-5 w-5 animate-spin rounded-full border-2 border-info/30 border-t-info" />
                    </div>
                  ) : (
                    <div
                      className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-md border ${
                        t.status === "failed"
                          ? "border-destructive/20 bg-destructive-subtle"
                          : "border-border bg-muted/30"
                      }`}
                    >
                      <ImageIcon
                        aria-hidden
                        className={`h-5 w-5 ${
                          t.status === "failed"
                            ? "text-destructive/50"
                            : "text-muted-foreground/30"
                        }`}
                      />
                    </div>
                  )}

                  <div className="min-w-0 flex-1">
                    <div className="flex min-w-0 flex-wrap items-center gap-2">
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

                  {isSelected && (
                    <div className="mr-1 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                  )}
                </button>
              </div>
            );
          })
        )}
      </div>

      {selectedTask && (
        <div>
          <button
            onClick={() => setDetailOpen(!detailOpen)}
            className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted/50"
          >
            {detailOpen ? (
              <ChevronDown className="h-3.5 w-3.5" />
            ) : (
              <ChevronRight className="h-3.5 w-3.5" />
            )}
            {zh.detail.taskDetail}
          </button>
          {detailOpen && (
            <div className="mt-2 space-y-2 px-1">
              <div className="rounded-xl border border-border bg-muted/30 p-4 font-mono text-[13px] leading-relaxed">
                <div className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1">
                  <span className="text-muted-foreground">任务 ID</span>
                  <span className="select-all text-foreground">
                    {selectedTask.request_id}
                  </span>
                  <span className="text-muted-foreground">批次 ID</span>
                  <span className="select-all text-foreground">
                    {selectedTask.batch_id}
                  </span>
                  <span className="text-muted-foreground">状态</span>
                  <span>
                    <StatusBadge status={selectedTask.status} />
                  </span>
                  <span className="text-muted-foreground">创建时间</span>
                  <span className="text-foreground">{selectedTask.created_at}</span>
                  <span className="text-muted-foreground">输入文件</span>
                  <span className="truncate text-foreground">
                    {selectedTask.input_filename}
                  </span>
                  <span className="text-muted-foreground">输出文件</span>
                  <span className="truncate text-foreground">
                    {selectedTask.output_path ?? "—"}
                  </span>
                  <span className="text-muted-foreground">模型</span>
                  <span className="text-foreground">{selectedTask.model_id}</span>
                  <span className="text-muted-foreground">输出尺寸</span>
                  <span className="text-foreground">
                    {selectedTask.output_size_label || selectedTask.output_size_preset}
                  </span>
                  <span className="text-muted-foreground">保存格式</span>
                  <span className="text-foreground">{selectedTask.output_format}</span>
                  <span className="text-muted-foreground">耗时</span>
                  <span className="text-foreground">
                    {formatElapsed(selectedTask.elapsed_seconds)}
                  </span>
                  {selectedTask.error_code && (
                    <>
                      <span className="text-destructive">错误代码</span>
                      <span className="text-destructive">{selectedTask.error_code}</span>
                    </>
                  )}
                </div>
              </div>
              <p className="text-xs text-muted-foreground">{zh.detail.deleteNote}</p>
            </div>
          )}
        </div>
      )}

      <div className="flex gap-2">
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

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3 text-sm">
          <span className="font-medium text-foreground">当前结果与任务</span>
          <span className="font-mono text-muted-foreground">
            {filteredTasks.length} 个
            {filteredTasks.length !== tasks.length && (
              <span className="text-muted-foreground/50"> / 共 {tasks.length}</span>
            )}
            {" · "}完成 {statusCounts.completed} · 失败 {statusCounts.failed}
          </span>
        </div>
        <button
          onClick={onRefresh}
          disabled={disabled}
          className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-2 text-xs font-medium text-muted-foreground transition-colors hover:border-accent hover:bg-accent-subtle hover:text-accent disabled:pointer-events-none disabled:opacity-40"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          刷新
        </button>
      </div>

      {partialBatchText && (
        <div className="rounded-lg border border-warning/30 bg-warning-subtle px-3 py-2 text-xs leading-relaxed text-warning">
          {partialBatchText}
        </div>
      )}

      <div className="space-y-4">
        <section className="space-y-2">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-medium text-foreground">
              {zh.panels.receipt.title}
            </h2>
            {selectedTask?.status === "completed" && (
              <span className="text-xs text-success">已完成</span>
            )}
          </div>
          {resultContent}
        </section>

        <section className="space-y-2">
          {taskListContent}
        </section>

        {selectedId && (
          <section className="space-y-2">
            <h2 className="text-sm font-medium text-foreground">
              {zh.panels.log.title}
            </h2>
            <RequestLogs requestId={selectedId} excerpt={logExcerpt} />
          </section>
        )}
      </div>
    </div>
  );
}
