import { Loader2 } from "lucide-react";
import type { TaskStatus } from "@/lib/types";
import { zh } from "@/i18n/zh";

const badgeStyles: Record<TaskStatus, { dot: string; cls: string; icon: string }> = {
  queued: {
    dot: "●",
    cls: "bg-muted text-muted-foreground",
    icon: "",
  },
  running: {
    dot: "",
    cls: "bg-info-subtle text-info",
    icon: "animate-spin",
  },
  completed: {
    dot: "✓",
    cls: "bg-success-subtle text-success",
    icon: "",
  },
  failed: {
    dot: "✕",
    cls: "bg-destructive-subtle text-destructive",
    icon: "",
  },
  deleted: {
    dot: "◌",
    cls: "bg-muted text-muted-foreground/60",
    icon: "",
  },
  interrupted: {
    dot: "◐",
    cls: "bg-warning-subtle text-warning",
    icon: "",
  },
};

interface StatusBadgeProps {
  status: TaskStatus;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const s = badgeStyles[status];

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${s.cls}`}
    >
      {s.icon ? (
        <Loader2 className={`h-3 w-3 ${s.icon}`} />
      ) : (
        <span className="text-[10px]" aria-hidden>
          {s.dot}
        </span>
      )}
      {zh.taskStatus[status]}
    </span>
  );
}
