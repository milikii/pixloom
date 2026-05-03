"use client";

import { FileText } from "lucide-react";
import { zh } from "@/i18n/zh";

interface RequestLogsProps {
  requestId: string | null;
  excerpt: string | null;
  loading?: boolean;
}

export function RequestLogs({
  requestId,
  excerpt,
  loading,
}: RequestLogsProps) {
  if (!requestId) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <FileText className="h-8 w-8 text-muted-foreground/50" />
        <p className="mt-3 text-sm text-muted-foreground">
          {zh.empty.noLogs}
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="animate-pulse space-y-2 py-4">
        <div className="h-3 w-3/4 rounded bg-muted" />
        <div className="h-3 w-1/2 rounded bg-muted" />
        <div className="h-3 w-2/3 rounded bg-muted" />
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border bg-muted/30 p-4">
      <pre className="whitespace-pre-wrap break-all font-mono text-xs leading-relaxed text-foreground">
        {excerpt || zh.empty.noLogs}
      </pre>
    </div>
  );
}
