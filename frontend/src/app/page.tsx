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
import { ResultsTabs } from "@/components/results/ResultsTabs";
import {
  TaskStatusDisplay,
  OutputPreview,
} from "@/components/tasks/TaskDetail";
import { TaskPanel } from "@/components/tasks/TaskPanel";
import { RequestLogs } from "@/components/logs/RequestLogs";
import { useModels } from "@/hooks/useModels";
import { useTasks, useTaskDelete, useRequestLog } from "@/hooks/useTasks";
import { useFileUpload, useSubmitBatch } from "@/hooks/useSubmitBatch";
import type { TaskRecord, ResolvedModel } from "@/lib/types";
import { zh } from "@/i18n/zh";

export default function HomePage() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [modelId, setModelId] = useState<string | null>(null);
  const [outputFormat, setOutputFormat] = useState("PNG");
  const [quality, setQuality] = useState(90);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState("");
  const [submitError, setSubmitError] = useState("");

  const { data: modelData } = useModels();
  const { data: taskData } = useTasks(60);
  const { data: logData, isLoading: logLoading } =
    useRequestLog(selectedTaskId);
  const fileUpload = useFileUpload();
  const submitBatch = useSubmitBatch();
  const taskDelete = useTaskDelete();

  const models = modelData?.models ?? [];
  const tasks = taskData?.tasks ?? [];
  const summary = taskData?.summary ?? {
    total: 0, queued: 0, running: 0, completed: 0,
    failed: 0, deleted: 0, interrupted: 0, cleanup_text: "",
  };
  const hiddenCount = modelData?.hidden_count ?? 0;
  const installedCount = models.length + hiddenCount;

  const selectedTask: TaskRecord | null =
    tasks.find((t) => t.request_id === selectedTaskId) ?? null;

  const handleSubmit = useCallback(async () => {
    if (selectedFiles.length === 0 || !modelId) return;
    setSubmitError("");
    setStatusMessage("");

    try {
      const uploadResult = await fileUpload.mutateAsync(selectedFiles);
      const storedPaths = uploadResult.uploaded.map((u) => u.stored_path);
      const batchResult = await submitBatch.mutateAsync({
        stored_paths: storedPaths,
        model_id: modelId,
        output_format: outputFormat,
        quality,
      });
      setStatusMessage(batchResult.status_message);
      setSelectedTaskId(batchResult.first_request_id);
      setSelectedFiles([]);
    } catch (err) {
      setSubmitError(
        err instanceof Error ? err.message : zh.toast.submitFailed
      );
    }
  }, [selectedFiles, modelId, outputFormat, quality, fileUpload, submitBatch]);

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
    <div className="mx-auto max-w-[1380px] px-4 pb-10 pt-5">
      <div className="mb-4 flex items-center justify-end">
        <ThemeToggle />
      </div>

      <ShellHeader
        operatorCount={models.length}
        installedCount={installedCount}
        hiddenCount={hiddenCount}
      />

      <div className="grid gap-4 lg:grid-cols-[5fr_6fr]">
        {/* LEFT: Submission */}
        <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
          <PanelHead
            eyebrow={zh.panels.input.eyebrow}
            title={zh.panels.input.title}
            copy={zh.panels.input.copy}
          />
          <UploadZone
            onFilesChange={setSelectedFiles}
            disabled={isSubmitting}
          />

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

          <PanelHead
            eyebrow={zh.panels.output.eyebrow}
            title={zh.panels.output.title}
            copy={zh.panels.output.copy}
          />
          <OutputParams
            format={outputFormat}
            quality={quality}
            onFormatChange={setOutputFormat}
            onQualityChange={setQuality}
          />

          {submitError && (
            <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-destructive dark:border-red-500/20 dark:bg-red-500/10">
              {submitError}
            </div>
          )}

          <SubmitButton
            onClick={handleSubmit}
            loading={isSubmitting}
            disabled={selectedFiles.length === 0 || !modelId}
          />
        </div>

        {/* RIGHT: Results */}
        <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
          <ResultsTabs
            tabs={[
              {
                key: "result",
                label: zh.tabs.result,
                content: (
                  <div className="space-y-4">
                    <div>
                      <label className="mb-1.5 block text-xs font-medium text-muted-foreground">
                        批次回执
                      </label>
                      <div className="rounded-xl border border-border bg-muted/30 p-4">
                        <pre className="whitespace-pre-wrap font-mono text-[13px] leading-relaxed text-foreground">
                          {statusMessage || "等待提交…"}
                        </pre>
                      </div>
                    </div>

                    <div>
                      <label className="mb-1.5 block text-xs font-medium text-muted-foreground">
                        当前任务状态
                      </label>
                      <div className="rounded-xl border border-border bg-muted/30 p-4">
                        <TaskStatusDisplay task={selectedTask} />
                      </div>
                    </div>

                    <OutputPreview
                      outputPath={selectedTask?.output_path ?? null}
                      requestId={selectedTaskId ?? ""}
                    />
                  </div>
                ),
              },
              {
                key: "tasks",
                label: zh.tabs.tasks,
                content: (
                  <TaskPanel
                    tasks={tasks}
                    summary={summary}
                    selectedTask={selectedTask}
                    selectedId={selectedTaskId}
                    onSelect={setSelectedTaskId}
                    onRefresh={() => {}}
                    onDelete={handleDelete}
                    deletePending={taskDelete.isPending}
                  />
                ),
              },
              {
                key: "logs",
                label: zh.tabs.logs,
                content: (
                  <RequestLogs
                    requestId={selectedTaskId}
                    excerpt={logData?.excerpt ?? null}
                    loading={logLoading}
                  />
                ),
              },
            ]}
          />
        </div>
      </div>
    </div>
  );
}
