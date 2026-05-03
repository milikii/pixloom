"use client";

import { useRef, useState } from "react";
import { Upload, X } from "lucide-react";
import { zh } from "@/i18n/zh";

interface SelectedFile {
  file: File;
  id: string;
}

interface UploadZoneProps {
  onFilesChange: (files: File[]) => void;
  disabled?: boolean;
}

export function UploadZone({ onFilesChange, disabled }: UploadZoneProps) {
  const [selectedFiles, setSelectedFiles] = useState<SelectedFile[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function updateFiles(files: File[]) {
    const withIds = files.map((f) => ({
      file: f,
      id: `${f.name}-${Date.now()}-${Math.random().toString(36).slice(2)}`,
    }));
    setSelectedFiles((prev) => [...prev, ...withIds]);
    onFilesChange([...selectedFiles.map((s) => s.file), ...files]);
  }

  function removeFile(id: string) {
    const next = selectedFiles.filter((f) => f.id !== id);
    setSelectedFiles(next);
    onFilesChange(next.map((f) => f.file));
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setIsDragOver(false);
    if (disabled) return;
    const files = Array.from(e.dataTransfer.files).filter((f) =>
      /\.(png|jpe?g|webp)$/i.test(f.name)
    );
    if (files.length > 0) updateFiles(files);
  }

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? []);
    if (files.length > 0) updateFiles(files);
    if (inputRef.current) inputRef.current.value = "";
  }

  function formatSize(bytes: number) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  return (
    <div className="mb-5">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`cursor-pointer rounded-xl border-2 border-dashed p-8 text-center transition-colors duration-150 ${
          isDragOver
            ? "border-accent bg-accent-subtle"
            : "border-border bg-muted/30 hover:border-accent hover:bg-accent-subtle"
        } ${disabled ? "pointer-events-none opacity-50" : ""}`}
      >
        <Upload className="mx-auto h-8 w-8 text-muted-foreground" />
        <p className="mt-3 text-sm text-muted-foreground">
          {zh.upload.placeholder}
        </p>
        <p className="mt-1 text-xs text-muted-foreground/70">
          {zh.upload.formats}
        </p>
        <p className="mt-0.5 text-xs text-muted-foreground/60">
          {zh.upload.maxSize}
        </p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".png,.jpg,.jpeg,.webp"
          onChange={handleChange}
          className="hidden"
        />
      </div>

      {selectedFiles.length > 0 && (
        <div className="mt-3 space-y-1.5">
          <p className="text-xs font-medium text-muted-foreground">
            {zh.upload.selected.replace("{count}", String(selectedFiles.length))}
          </p>
          {selectedFiles.map(({ file, id }) => (
            <div
              key={id}
              className="flex items-center justify-between rounded-lg bg-muted/50 px-3 py-2 text-sm"
            >
              <span className="truncate text-foreground">{file.name}</span>
              <span className="mx-2 shrink-0 text-xs text-muted-foreground">
                {formatSize(file.size)}
              </span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  removeFile(id);
                }}
                className="shrink-0 rounded p-0.5 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
                aria-label={`${zh.upload.remove} ${file.name}`}
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
