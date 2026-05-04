"use client";

import { Download } from "lucide-react";
import type { TaskRecord } from "@/lib/types";
import { zh } from "@/i18n/zh";
import { StatusBadge } from "./StatusBadge";

function formatElapsed(seconds: number | null) {
  if (seconds === null || seconds === undefined) return "—";
  if (seconds < 60) return `${seconds.toFixed(1)} 秒`;
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m} 分 ${s} 秒`;
}

export function TaskDetail({ task }: { task: TaskRecord }) {
  return (
    <div className="rounded-xl border border-border bg-muted/30 p-4 font-mono text-[13px] leading-relaxed">
      <div className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1">
        <span className="text-muted-foreground">任务 ID</span>
        <span className="select-all text-foreground">{task.request_id}</span>

        <span className="text-muted-foreground">批次 ID</span>
        <span className="select-all text-foreground">{task.batch_id}</span>

        <span className="text-muted-foreground">状态</span>
        <span><StatusBadge status={task.status} /></span>

        <span className="text-muted-foreground">创建时间</span>
        <span className="text-foreground">{task.created_at}</span>

        <span className="text-muted-foreground">输入文件</span>
        <span className="truncate text-foreground">{task.input_filename}</span>

        <span className="text-muted-foreground">输出文件</span>
        <span className="truncate text-foreground">
          {task.output_path ?? "—"}
        </span>

        <span className="text-muted-foreground">模型</span>
        <span className="text-foreground">{task.model_id}</span>

        <span className="text-muted-foreground">输出尺寸</span>
        <span className="text-foreground">
          {task.output_size_label || task.output_size_preset}
        </span>

        <span className="text-muted-foreground">保存格式</span>
        <span className="text-foreground">
          {task.output_format} · 质量 {task.quality}
        </span>

        <span className="text-muted-foreground">阶段</span>
        <span className="text-foreground">
          {task.progress_step || "—"}
        </span>

        <span className="text-muted-foreground">进度</span>
        <span className="text-foreground">
          {Math.round(task.progress_value * 100)}%
        </span>

        <span className="text-muted-foreground">耗时</span>
        <span className="text-foreground">
          {formatElapsed(task.elapsed_seconds)}
        </span>

        {task.error_code && (
          <>
            <span className="text-destructive">错误代码</span>
            <span className="text-destructive">{task.error_code}</span>
          </>
        )}
      </div>
      <p className="mt-3 border-t border-border pt-3 text-xs text-muted-foreground">
        {zh.detail.deleteNote}
      </p>
    </div>
  );
}

export function TaskStatusDisplay({ task }: { task: TaskRecord | null }) {
  if (!task) {
    return (
      <p className="text-sm text-muted-foreground">
        请上传图片、选择模型并提交。任务在后台串行处理。
      </p>
    );
  }

  return (
    <div className="space-y-2 font-mono text-[13px] leading-relaxed text-foreground">
      <p>
        <span className="text-muted-foreground">request_id: </span>
        {task.request_id}
      </p>
      <p>
        <StatusBadge status={task.status} />
      </p>
      <p>
        <span className="text-muted-foreground">模型: </span>
        {task.model_id}
      </p>
      {task.status === "running" && (
        <>
          <p>
            {Math.round(task.progress_value * 100)}% | {task.progress_step}
          </p>
          {task.eta_seconds !== null && (
            <p className="text-muted-foreground">
              预计剩余 {formatElapsed(task.eta_seconds)}
            </p>
          )}
        </>
      )}
      {task.status === "completed" && (
        <p className="text-success">
          {zh.progress.processingComplete} | {formatElapsed(task.elapsed_seconds)}
        </p>
      )}
      {task.status === "failed" && (
        <p className="text-destructive">
          {task.error_code} — {task.error_detail || "未知错误"}
        </p>
      )}
    </div>
  );
}

export function OutputPreview({
  outputPath,
  requestId,
}: {
  outputPath: string | null;
  requestId: string;
}) {
  if (!outputPath) {
    return (
      <div className="flex items-center justify-center rounded-xl border border-border bg-muted/30 py-16 text-sm text-muted-foreground">
        暂无预览
      </div>
    );
  }

  const name = outputPath.replace(/^.*[\\/]/, "");
  const url = `/api/files/output/${encodeURIComponent(name)}`;

  return (
    <div className="space-y-3">
      <div className="overflow-hidden rounded-xl border border-border bg-muted/10">
        {/*
         * next/image can't be used for arbitrary API-served paths
         * without whitelisting in next.config.ts. Using <img> is fine
         * for an internal tool. */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={url}
          alt={`Upscale result for ${requestId}`}
          className="w-full"
        />
      </div>
      <a
        href={url}
        download
        className="inline-flex items-center gap-2 rounded-lg border border-border px-4 py-2.5 text-sm font-medium text-foreground transition-colors hover:bg-accent-subtle hover:border-accent hover:text-accent"
      >
        <Download className="h-4 w-4" />
        下载结果
      </a>
    </div>
  );
}
