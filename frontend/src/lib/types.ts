export interface ResolvedModel {
  id: string;
  display_name: string;
  display_name_zh: string;
  backend: string;
  architecture: string;
  scale: number;
  image_types: string[];
  recommended_for_zh: string;
  style_zh: string;
  speed_zh: string;
  stability_zh: string;
  warning_zh: string;
  sharp_review_zh: string;
  notes: string;
}

export interface ModelListResponse {
  models: ResolvedModel[];
  hidden_count: number;
}

export type TaskStatus =
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "deleted"
  | "interrupted";

export interface TaskRecord {
  request_id: string;
  batch_id: string;
  status: TaskStatus;
  status_label: string;
  input_filename: string;
  input_path: string;
  output_path: string | null;
  model_id: string;
  output_format: string;
  quality: number;
  output_size_preset: OutputSizePreset;
  output_size_label: string;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  elapsed_seconds: number | null;
  progress_value: number;
  progress_step: string;
  progress_summary: string;
  eta_seconds: number | null;
  error_code: string;
  error_detail: string;
}

export interface TaskSummary {
  total: number;
  queued: number;
  running: number;
  completed: number;
  failed: number;
  deleted: number;
  interrupted: number;
  cleanup_text: string;
}

export interface TaskListResponse {
  tasks: TaskRecord[];
  summary: TaskSummary;
}

export interface TaskDeleteResult {
  request_id: string;
  deleted_paths: string[];
  missing_paths: string[];
  skipped_paths: string[];
  message_zh: string;
}

export interface BatchCreateRequest {
  stored_paths: string[];
  model_id: string;
  output_format: string;
  quality: number;
  output_size_preset: OutputSizePreset;
}

export type OutputSizePreset = "native" | "2k" | "4k" | "8k";

export interface BatchCreateResponse {
  batch_id: string;
  tasks: TaskRecord[];
  queued_count: number;
  first_request_id: string;
  status_message: string;
  log_excerpt: string;
}

export interface UploadResponse {
  uploaded: Array<{
    original_name: string;
    stored_path: string;
    size_bytes: number;
  }>;
}

export interface LogExcerptResponse {
  request_id: string;
  excerpt: string;
}

export interface ErrorDetail {
  request_id: string;
  code: string;
  user_message_zh: string;
  likely_cause_zh: string;
  suggested_action_zh: string;
}
