"use client";

import { useCallback, useState } from "react";
import { ShellHeader } from "@/components/shell/ShellHeader";
import { ThemeToggle } from "@/components/shell/ThemeToggle";
import { PanelHead } from "@/components/shell/PanelHead";
import { UploadZone } from "@/components/submission/UploadZone";
import { ModelPicker } from "@/components/submission/ModelPicker";
import { ModelGuidance } from "@/components/submission/ModelGuidance";
import { OutputParams } from "@/components/submission/OutputParams";
import { SubmitButton } from "@/components/submission/SubmitButton";
import { TaskPanel } from "@/components/tasks/TaskPanel";
import { useModels } from "@/hooks/useModels";
import { useTasks, useTaskDelete, useRequestLog } from "@/hooks/useTasks";
import { useFileUpload, useSubmitBatch } from "@/hooks/useSubmitBatch";
import type { TaskRecord, ResolvedModel, OutputSizePreset } from "@/lib/types";
import { zh } from "@/i18n/zh";

export default function HomePage() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [modelId, setModelId] = useState<string | null>(null);
  const [outputFormat, setOutputFormat] = useState("PNG");
  const [outputSizePreset, setOutputSizePreset] =
    useState<OutputSizePreset>("native");
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState("");

  const { data: modelData } = useModels();
  const { data: taskData, refetch: refetchTasks } = useTasks(60);
  const { data: logData } =
    useRequestLog(selectedTaskId);
  const fileUpload = useFileUpload();
  const submitBatch = useSubmitBatch();
  const taskDelete = useTaskDelete();

  const models = modelData?.models ?? [];
  const tasks = taskData?.tasks ?? [];
  const hiddenCount = modelData?.hidden_count ?? 0;
  const installedCount = models.length + hiddenCount;

  const selectedTask: TaskRecord | null =
    tasks.find((t) => t.request_id === selectedTaskId) ?? null;

  const handleSubmit = useCallback(async () => {
    if (selectedFiles.length === 0 || !modelId) return;
    setSubmitError("");

    try {
      const uploadResult = await fileUpload.mutateAsync(selectedFiles);
      const storedPaths = uploadResult.uploaded.map((u) => u.stored_path);
      const batchResult = await submitBatch.mutateAsync({
        stored_paths: storedPaths,
        model_id: modelId,
        output_format: outputFormat,
        output_size_preset: outputSizePreset,
      });
      setSelectedTaskId(batchResult.first_request_id);
      setSelectedFiles([]);
    } catch (err) {
      setSubmitError(
        err instanceof Error ? err.message : zh.toast.submitFailed
      );
    }
  }, [
    selectedFiles,
    modelId,
    outputFormat,
    outputSizePreset,
    fileUpload,
    submitBatch,
  ]);

  const handleDelete = useCallback(() => {
    if (!selectedTaskId) return;
    taskDelete.mutate(selectedTaskId, {
      onSuccess: () => setSelectedTaskId(null),
    });
  }, [selectedTaskId, taskDelete]);

  const isSubmitting = fileUpload.isPending || submitBatch.isPending;
  const guidanceModel: ResolvedModel | null =
    models.find((m) => m.id === modelId) ?? null;

  return (
    <div className="mx-auto max-w-[1380px] px-3 pb-8 pt-4 sm:px-4 sm:pb-10 sm:pt-5">
      <ShellHeader
        operatorCount={models.length}
        installedCount={installedCount}
        rightSlot={<ThemeToggle variant="header" />}
      />

      <div className="grid min-w-0 gap-3 sm:gap-4 lg:grid-cols-[5fr_6fr]">
        {/* LEFT: Submission */}
        <div className="min-w-0 rounded-xl border border-border bg-surface p-4 shadow-card transition-all duration-200 hover:-translate-y-px hover:shadow-card-hover sm:rounded-2xl sm:p-5">
          <PanelHead
            eyebrow={zh.panels.input.eyebrow}
            title={zh.panels.input.title}
            copy={zh.panels.input.copy}
          />
          <UploadZone
            onFilesChange={setSelectedFiles}
            disabled={isSubmitting}
          />

          <div className="rounded-xl border border-border/80 bg-muted/20 px-4 py-4">
            <PanelHead
              eyebrow={zh.panels.model.eyebrow}
              title={zh.panels.model.title}
              copy={zh.panels.model.copy}
            />
            <ModelPicker
              models={models}
              selectedId={modelId}
              onSelect={setModelId}
              disabled={isSubmitting}
            />

            <ModelGuidance
              model={guidanceModel}
              hiddenCount={hiddenCount}
              hasLocalModels={installedCount > 0}
              hasSelectedModel={!!modelId}
            />
          </div>

          <div className="rounded-xl border border-border/80 bg-muted/20 px-4 py-4">
            <PanelHead
              eyebrow={zh.panels.output.eyebrow}
              title={zh.panels.output.title}
              copy={zh.panels.output.copy}
            />
            <OutputParams
              format={outputFormat}
              outputSizePreset={outputSizePreset}
              onFormatChange={setOutputFormat}
              onOutputSizePresetChange={setOutputSizePreset}
            />
          </div>

          {submitError && (
            <div className="mb-4 rounded-lg border border-destructive-subtle bg-destructive-subtle px-4 py-3 text-sm text-destructive">
              {submitError}
            </div>
          )}

          <SubmitButton
            onClick={handleSubmit}
            loading={isSubmitting}
            disabled={selectedFiles.length === 0 || !modelId}
          />
        </div>

        {/* RIGHT: Tasks + Preview */}
        <div className="min-w-0 rounded-xl border border-border bg-surface p-4 shadow-card transition-all duration-200 hover:-translate-y-px hover:shadow-card-hover sm:rounded-2xl sm:p-5">
          <TaskPanel
            tasks={tasks}
            selectedTask={selectedTask}
            selectedId={selectedTaskId}
            onSelect={setSelectedTaskId}
            onRefresh={() => refetchTasks()}
            onDelete={handleDelete}
            deletePending={taskDelete.isPending}
            logExcerpt={logData?.excerpt ?? null}
          />
        </div>
      </div>
    </div>
  );
}
