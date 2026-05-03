"use client";

import { Loader2 } from "lucide-react";
import { zh } from "@/i18n/zh";

interface SubmitButtonProps {
  onClick: () => void;
  loading?: boolean;
  disabled?: boolean;
}

export function SubmitButton({
  onClick,
  loading,
  disabled,
}: SubmitButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      className="w-full rounded-lg bg-accent py-3.5 text-[15px] font-semibold text-white shadow-sm transition-all duration-200 hover:-translate-y-px hover:shadow-md hover:shadow-accent/25 active:translate-y-0 active:scale-[0.99] disabled:pointer-events-none disabled:opacity-40"
    >
      {loading ? (
        <span className="inline-flex items-center gap-2">
          <Loader2 className="h-4 w-4 animate-spin" />
          {zh.submit.loading}
        </span>
      ) : (
        zh.submit.label
      )}
    </button>
  );
}
