interface PanelHeadProps {
  eyebrow: string;
  title: string;
  copy: string;
}

export function PanelHead({ eyebrow, title, copy }: PanelHeadProps) {
  return (
    <div className="mb-3">
      <p className="text-[10px] font-medium uppercase tracking-widest text-accent">
        {eyebrow}
      </p>
      <h2 className="mt-0.5 text-base font-semibold text-foreground sm:text-lg">
        {title}
      </h2>
      <p className="mt-1 text-[12px] leading-relaxed text-muted-foreground sm:text-[13px]">
        {copy}
      </p>
    </div>
  );
}
