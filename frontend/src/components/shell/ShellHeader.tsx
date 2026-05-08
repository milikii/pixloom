import { zh } from "@/i18n/zh";
import type { ReactNode } from "react";

export function ShellMetric({
  value,
  label,
}: {
  value: number;
  label: string;
}) {
  return (
    <div className="rounded-xl border border-white/8 bg-white/[0.04] px-3 py-3 backdrop-blur-sm sm:px-5 sm:py-4">
      <span className="block text-xl font-bold tabular-nums tracking-tight text-accent sm:text-2xl">
        {value}
      </span>
      <span className="mt-0.5 block text-[10px] font-medium uppercase tracking-widest text-header-muted sm:text-[11px]">
        {label}
      </span>
    </div>
  );
}

export function ShellHeader({
  operatorCount,
  installedCount,
  hiddenCount,
  rightSlot,
}: {
  operatorCount: number;
  installedCount: number;
  hiddenCount: number;
  rightSlot?: ReactNode;
}) {
  const { shell } = zh;
  return (
    <header className="relative mb-4 overflow-hidden rounded-2xl border border-white/[0.06] bg-header px-4 pb-4 pt-4 shadow-2xl sm:mb-6 sm:px-6 sm:pb-6 sm:pt-6">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(91,95,239,0.08),transparent_50%)]" />
      <div className="relative">
        <div className="flex flex-wrap items-start justify-between gap-3 sm:gap-4">
          <div>
            <p className="text-[10px] font-medium uppercase tracking-widest text-header-muted sm:text-[11px]">
              {shell.label}
            </p>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-header-text sm:text-3xl">
              {shell.title}
            </h1>
            <p className="mt-1.5 max-w-xl text-[12px] leading-relaxed text-header-secondary sm:mt-2 sm:text-[13px]">
              {shell.copy}
            </p>
          </div>
          {rightSlot && <div className="shrink-0">{rightSlot}</div>}
        </div>
        <div className="mt-4 grid grid-cols-2 gap-2 sm:mt-5 sm:gap-3">
          <ShellMetric value={operatorCount} label={shell.metrics.operator} />
          <ShellMetric value={installedCount} label={shell.metrics.installed} />
        </div>
        {hiddenCount > 0 && (
          <p className="mt-3 text-[12px] leading-relaxed text-header-secondary">
            {zh.model.hiddenNote.replace("{count}", String(hiddenCount))}
          </p>
        )}
      </div>
    </header>
  );
}
