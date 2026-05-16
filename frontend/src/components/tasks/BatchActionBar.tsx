"use client";

import { CheckSquare, Download, X } from "lucide-react";

interface BatchActionBarProps {
  selectedIds: Set<string>;
  selectableCount: number;
  allSelected: boolean;
  downloadPending: boolean;
  onSelectAll: () => void;
  onDownload: () => void;
  onClear: () => void;
}

export function BatchActionBar({
  selectedIds,
  selectableCount,
  allSelected,
  downloadPending,
  onSelectAll,
  onDownload,
  onClear,
}: BatchActionBarProps) {
  if (selectableCount === 0) return null;

  return (
    <div className="flex flex-wrap items-center gap-2 rounded-lg border border-accent/30 bg-accent-subtle px-3 py-2">
      <span className="text-xs font-medium text-accent">
        已选 {selectedIds.size} / {selectableCount} 项
      </span>
      <button
        onClick={onSelectAll}
        disabled={allSelected}
        className="inline-flex items-center gap-1.5 rounded-md border border-accent/25 px-3 py-1 text-xs font-medium text-accent transition-colors hover:bg-accent/10 disabled:pointer-events-none disabled:opacity-55"
      >
        <CheckSquare className="h-3.5 w-3.5" />
        {allSelected ? "已全选" : "全选当前列表"}
      </button>
      <button
        onClick={onDownload}
        disabled={selectedIds.size === 0 || downloadPending}
        className="inline-flex items-center gap-1.5 rounded-md bg-accent px-3 py-1 text-xs font-medium text-white transition-colors hover:bg-accent-hover disabled:pointer-events-none disabled:opacity-45"
      >
        <Download className="h-3.5 w-3.5" />
        {downloadPending ? "正在打包" : "下载所选"}
      </button>
      {selectedIds.size > 0 && (
        <button
          onClick={onClear}
          className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted-foreground transition-colors hover:text-foreground"
        >
          <X className="h-3.5 w-3.5" />
          取消选择
        </button>
      )}
    </div>
  );
}
