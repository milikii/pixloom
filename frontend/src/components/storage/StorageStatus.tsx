"use client";

import {
  Archive,
  Cpu,
  Database,
  FileText,
  HardDrive,
  Image as ImageIcon,
  Layers,
  Upload,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { StorageCategory, StorageSnapshot } from "@/lib/types";

const CATEGORY_ICONS: Record<StorageCategory["key"], LucideIcon> = {
  models: Cpu,
  input: Upload,
  output: ImageIcon,
  thumbnails: Layers,
  logs: FileText,
  state: Database,
  archives: Archive,
};

function formatBytes(bytes: number) {
  if (!Number.isFinite(bytes) || bytes <= 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let value = bytes;
  let index = 0;
  while (value >= 1024 && index < units.length - 1) {
    value /= 1024;
    index += 1;
  }
  const digits = value >= 10 || index === 0 ? 0 : 1;
  return `${value.toFixed(digits)} ${units[index]}`;
}

function categoryBarWidth(category: StorageCategory) {
  if (category.bytes <= 0) return "0%";
  return `${Math.max(2, Math.min(100, category.percent_of_managed))}%`;
}

interface StorageStatusProps {
  snapshot: StorageSnapshot | undefined;
  loading?: boolean;
}

export function StorageStatus({ snapshot, loading }: StorageStatusProps) {
  if (!snapshot) {
    return (
      <section className="mt-4 rounded-xl border border-border/80 bg-muted/20 px-4 py-4">
        <div className="flex items-center gap-2 text-sm font-medium text-foreground">
          <HardDrive className="h-4 w-4 text-accent" />
          存储状态
        </div>
        <div className="mt-3 h-16 animate-pulse rounded-lg bg-muted" />
        <p className="mt-2 text-[12px] text-muted-foreground">
          {loading ? "正在读取本地存储占用..." : "暂时无法读取存储状态。"}
        </p>
      </section>
    );
  }

  const diskWarning = snapshot.disk.used_percent >= 85;
  const topCategories = [...snapshot.categories].sort((a, b) => b.bytes - a.bytes);

  return (
    <section className="mt-4 rounded-xl border border-border/80 bg-muted/20 px-4 py-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <HardDrive className="h-4 w-4 text-accent" />
          <h2 className="text-sm font-semibold text-foreground">存储状态</h2>
        </div>
        <div className="text-right font-mono text-[12px] text-muted-foreground">
          <div>{formatBytes(snapshot.total_managed_bytes)}</div>
          <div>托管文件</div>
        </div>
      </div>

      <div className="mt-3 rounded-lg border border-border bg-surface/60 px-3 py-3">
        <div className="flex items-center justify-between gap-3 text-[12px]">
          <span className="font-medium text-foreground">磁盘占用</span>
          <span className={diskWarning ? "text-warning" : "text-muted-foreground"}>
            {snapshot.disk.used_percent.toFixed(1)}% · 可用{" "}
            {formatBytes(snapshot.disk.free_bytes)}
          </span>
        </div>
        <div className="mt-2 h-2 overflow-hidden rounded-full bg-muted">
          <div
            className={`h-full rounded-full ${
              diskWarning ? "bg-warning" : "bg-accent"
            }`}
            style={{ width: `${Math.min(100, snapshot.disk.used_percent)}%` }}
          />
        </div>
        <p className="mt-2 text-[11px] leading-relaxed text-muted-foreground">
          {snapshot.retention.message_zh}
        </p>
      </div>

      <div className="mt-3 grid gap-2 sm:grid-cols-2">
        {topCategories.map((category) => {
          const Icon = CATEGORY_ICONS[category.key];
          return (
            <div
              key={category.key}
              className="min-w-0 rounded-lg border border-border/70 bg-surface/50 px-3 py-2.5"
              title={category.description_zh}
            >
              <div className="flex items-center gap-2">
                <Icon className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                <span className="min-w-0 flex-1 truncate text-[12px] font-medium text-foreground">
                  {category.label_zh}
                </span>
                <span className="shrink-0 font-mono text-[12px] text-muted-foreground">
                  {formatBytes(category.bytes)}
                </span>
              </div>
              <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-accent/70"
                  style={{ width: categoryBarWidth(category) }}
                />
              </div>
              <div className="mt-1.5 flex items-center justify-between gap-2 font-mono text-[11px] text-muted-foreground/80">
                <span>{category.file_count} 个文件</span>
                <span>{category.percent_of_managed.toFixed(1)}%</span>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
