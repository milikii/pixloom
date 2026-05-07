"use client";

import {
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { useState } from "react";
import type { OutputSizePreset } from "@/lib/types";

interface OutputParamsProps {
  format: string;
  outputSizePreset: OutputSizePreset;
  onFormatChange: (f: string) => void;
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
  outputSizePreset,
  onFormatChange,
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
                  : "border-border bg-muted/60 text-foreground hover:border-accent/50"
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
        className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-foreground transition-colors hover:bg-muted/40"
      >
        保存参数
        {open ? (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-4 w-4 text-muted-foreground" />
        )}
      </button>
      {open && (
        <div className="space-y-4 border-t border-border px-4 pb-4 pt-3">
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
                      : "bg-muted/60 text-muted-foreground hover:bg-accent-subtle hover:text-accent"
                  }`}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>
          <p className="text-xs text-muted-foreground">
            JPG / WEBP 质量固定为 100，不再单独调节。
          </p>
        </div>
      )}
    </div>
  );
}
