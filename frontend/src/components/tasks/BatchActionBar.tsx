"use client";

import { Download, X } from "lucide-react";

interface BatchActionBarProps {
  selectedIds: Set<string>;
  onDownload: () => void;
  onClear: () => void;
}

export function BatchActionBar({
  selectedIds,
  onDownload,
  onClear,
}: BatchActionBarProps) {
  if (selectedIds.size === 0) return null;

  return (
    <div className="flex items-center gap-3 rounded-lg border border-accent/30 bg-accent-subtle px-3 py-2">
      <span className="text-xs font-medium text-accent">
        已选 {selectedIds.size} 项
      </span>
      <button
        onClick={onDownload}
        className="inline-flex items-center gap-1.5 rounded-md bg-accent px-3 py-1 text-xs font-medium text-white transition-colors hover:bg-accent-hover"
      >
        <Download className="h-3.5 w-3.5" />
        下载所选
      </button>
      <button
        onClick={onClear}
        className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted-foreground transition-colors hover:text-foreground"
      >
        <X className="h-3.5 w-3.5" />
        取消选择
      </button>
    </div>
  );
}

/** Trigger browser downloads for a list of output URLs. */
export function downloadFiles(urls: string[]) {
  for (const url of urls) {
    const a = document.createElement("a");
    a.href = url;
    a.download = "";
    a.target = "_blank";
    a.click();
  }
}
