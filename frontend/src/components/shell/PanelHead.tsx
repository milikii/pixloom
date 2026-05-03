interface PanelHeadProps {
  eyebrow: string;
  title: string;
  copy: string;
}

export function PanelHead({ eyebrow, title, copy }: PanelHeadProps) {
  return (
    <div className="mb-4">
      <p className="text-[11px] font-medium uppercase tracking-widest text-accent">
        {eyebrow}
      </p>
      <h2 className="mt-0.5 text-lg font-semibold text-foreground">
        {title}
      </h2>
      <p className="mt-1 text-[13px] leading-relaxed text-muted-foreground">
        {copy}
      </p>
    </div>
  );
}
