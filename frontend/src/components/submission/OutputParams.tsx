"use client";

import {
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { useState } from "react";
import { zh } from "@/i18n/zh";

interface OutputParamsProps {
  format: string;
  quality: number;
  onFormatChange: (f: string) => void;
  onQualityChange: (q: number) => void;
}

const FORMATS = ["PNG", "JPG", "WEBP"];

export function OutputParams({
  format,
  quality,
  onFormatChange,
  onQualityChange,
}: OutputParamsProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="mb-5 overflow-hidden rounded-xl border border-border bg-surface">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-foreground transition-colors hover:bg-muted/50"
      >
        输出参数
        {open ? (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-4 w-4 text-muted-foreground" />
        )}
      </button>
      {open && (
        <div className="border-t border-border px-4 pb-4 pt-3 space-y-4">
          <div>
            <label className="mb-2 block text-xs font-medium text-muted-foreground">
              输出格式
            </label>
            <div className="flex gap-2">
              {FORMATS.map((f) => (
                <button
                  key={f}
                  onClick={() => onFormatChange(f)}
                  className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                    format === f
                      ? "bg-accent text-white shadow-sm"
                      : "bg-muted text-muted-foreground hover:bg-accent-subtle hover:text-accent"
                  }`}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="mb-2 flex items-center justify-between text-xs font-medium text-muted-foreground">
              <span>JPG / WEBP 质量</span>
              <span className="tabular-nums text-accent">{quality}</span>
            </label>
            <input
              type="range"
              min={1}
              max={100}
              value={quality}
              onChange={(e) => onQualityChange(Number(e.target.value))}
              className="w-full accent-accent"
            />
          </div>
        </div>
      )}
    </div>
  );
}
