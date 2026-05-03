import { zh } from "@/i18n/zh";

export function ShellMetric({
  value,
  label,
}: {
  value: number;
  label: string;
}) {
  return (
    <div className="rounded-xl border border-white/8 bg-white/[0.04] px-5 py-4 backdrop-blur-sm">
      <span className="block text-2xl font-bold tabular-nums tracking-tight text-accent">
        {value}
      </span>
      <span className="mt-0.5 block text-[11px] font-medium uppercase tracking-widest text-header-muted">
        {label}
      </span>
    </div>
  );
}

export function ShellHeader({
  operatorCount,
  installedCount,
  hiddenCount,
}: {
  operatorCount: number;
  installedCount: number;
  hiddenCount: number;
}) {
  const { shell } = zh;
  return (
    <header className="relative mb-6 overflow-hidden rounded-2xl border border-white/[0.06] bg-header px-6 pb-6 pt-6 shadow-2xl">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(91,95,239,0.08),transparent_50%)]" />
      <div className="relative">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-[11px] font-medium uppercase tracking-widest text-header-muted">
              {shell.label}
            </p>
            <h1 className="mt-1 text-3xl font-bold tracking-tight text-header-text">
              {shell.title}
            </h1>
            <p className="mt-2 max-w-xl text-[13px] leading-relaxed text-header-secondary">
              {shell.copy}
            </p>
          </div>
        </div>
        <div className="mt-5 grid grid-cols-3 gap-3">
          <ShellMetric value={operatorCount} label={shell.metrics.operator} />
          <ShellMetric value={installedCount} label={shell.metrics.installed} />
          <ShellMetric value={hiddenCount} label={shell.metrics.hidden} />
        </div>
      </div>
    </header>
  );
}
