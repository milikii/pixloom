"use client";

import {
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { useState } from "react";
import type { OutputSizePreset } from "@/lib/types";

interface OutputParamsProps {
  format: string;
  quality: number;
  outputSizePreset: OutputSizePreset;
  onFormatChange: (f: string) => void;
  onQualityChange: (q: number) => void;
  onOutputSizePresetChange: (preset: OutputSizePreset) => void;
}

const FORMATS = ["PNG", "JPG", "WEBP"];
const OUTPUT_SIZE_OPTIONS: Array<{
  value: OutputSizePreset;
  label: string;
  helper: string;
}> = [
  { value: "native", label: "原始", helper: "按模型倍率" },
  { value: "2k", label: "2K", helper: "最长边 2048px" },
  { value: "4k", label: "4K", helper: "最长边 4096px" },
  { value: "8k", label: "8K", helper: "最长边 8192px" },
];

export function OutputParams({
  format,
  quality,
  outputSizePreset,
  onFormatChange,
  onQualityChange,
  onOutputSizePresetChange,
}: OutputParamsProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="mb-5 overflow-hidden rounded-xl border border-border bg-surface">
      <div className="border-b border-border px-4 pb-4 pt-3">
        <label className="mb-2 block text-xs font-medium text-muted-foreground">
          输出尺寸
        </label>
        <div className="grid grid-cols-2 gap-2">
          {OUTPUT_SIZE_OPTIONS.map((option) => (
            <button
              key={option.value}
              onClick={() => onOutputSizePresetChange(option.value)}
              className={`min-h-14 rounded-lg border px-3 py-2 text-left transition-colors focus:outline-none focus:ring-2 focus:ring-accent/20 ${
                outputSizePreset === option.value
                  ? "border-accent bg-accent-subtle text-accent"
                  : "border-border bg-muted text-foreground hover:border-accent/50"
              }`}
            >
              <span className="block text-sm font-semibold">{option.label}</span>
              <span className="mt-0.5 block text-xs text-muted-foreground">
                {option.helper}
              </span>
            </button>
          ))}
        </div>
      </div>
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-foreground transition-colors hover:bg-muted/50"
      >
        保存参数
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
