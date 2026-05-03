import type {
  BatchCreateRequest,
  BatchCreateResponse,
  LogExcerptResponse,
  ModelGuidanceResponse,
  ModelListResponse,
  TaskListResponse,
  UploadResponse,
} from "./types";

const API_BASE = "/api";

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: {
      ...(options?.body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message =
      body?.detail?.user_message_zh ||
      body?.detail ||
      `Request failed: ${res.status}`;
    throw new Error(message);
  }

  return res.json();
}

export const apiClient = {
  getModels(): Promise<ModelListResponse> {
    return request("/models");
  },

  getModelGuidance(modelId: string): Promise<ModelGuidanceResponse> {
    return request(`/models/${modelId}/guidance`);
  },

  async uploadFiles(files: File[]): Promise<UploadResponse> {
    const formData = new FormData();
    files.forEach((f) => formData.append("files", f));
    return request("/upload", { method: "POST", body: formData });
  },

  createBatch(body: BatchCreateRequest): Promise<BatchCreateResponse> {
    return request("/batches", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  getTasks(limit = 60): Promise<TaskListResponse> {
    return request(`/tasks?limit=${limit}`);
  },

  deleteTask(requestId: string): Promise<{ message_zh: string }> {
    return request(`/tasks/${requestId}`, { method: "DELETE" });
  },

  getRequestLog(requestId: string): Promise<LogExcerptResponse> {
    return request(`/logs/${requestId}`);
  },
};
