import type {
  BatchCreateRequest,
  BatchCreateResponse,
  LogExcerptResponse,
  ModelListResponse,
  TaskDeleteResult,
  TaskListResponse,
  UploadResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "/api";

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
      (body?.detail?.code && body?.detail?.request_id
        ? `错误 [${body.detail.code}]，请求编号：${body.detail.request_id}`
        : "") ||
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

  async uploadFiles(files: File[]): Promise<UploadResponse> {
    const formData = new FormData();
    files.forEach((f) => formData.append("files", f));
    return request("/upload", { method: "POST", body: formData });
  },

  async createBatch(body: BatchCreateRequest): Promise<BatchCreateResponse> {
    const result = await request<BatchCreateResponse>("/batches", {
      method: "POST",
      body: JSON.stringify(body),
    });
    if (result.queued_count === 0) {
      throw new Error(result.status_message || "批次创建失败，请检查后重试。");
    }
    return result;
  },

  getTasks(limit = 60): Promise<TaskListResponse> {
    return request(`/tasks?limit=${limit}`);
  },

  deleteTask(requestId: string): Promise<TaskDeleteResult> {
    return request(`/tasks/${requestId}`, { method: "DELETE" });
  },

  getRequestLog(requestId: string): Promise<LogExcerptResponse> {
    return request(`/logs/${requestId}`);
  },
};
