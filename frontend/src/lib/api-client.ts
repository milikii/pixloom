import type {
  BatchCreateRequest,
  BatchCreateResponse,
  LogExcerptResponse,
  ModelListResponse,
  StorageSnapshot,
  TaskDeleteResult,
  TaskListResponse,
  UploadResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "/api";

function errorMessageFromBody(body: unknown, status: number): string {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail?: unknown }).detail;
    if (detail && typeof detail === "object") {
      const typed = detail as {
        user_message_zh?: string;
        code?: string;
        request_id?: string;
      };
      if (typed.user_message_zh) return typed.user_message_zh;
      if (typed.code && typed.request_id) {
        return `错误 [${typed.code}]，请求编号：${typed.request_id}`;
      }
    }
    if (typeof detail === "string") return detail;
  }
  return `Request failed: ${status}`;
}

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
    throw new Error(errorMessageFromBody(body, res.status));
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

  getStorage(): Promise<StorageSnapshot> {
    return request("/storage");
  },

  deleteTask(requestId: string): Promise<TaskDeleteResult> {
    return request(`/tasks/${requestId}`, { method: "DELETE" });
  },

  getRequestLog(requestId: string): Promise<LogExcerptResponse> {
    return request(`/logs/${requestId}`);
  },

  taskArchiveUrl(requestIds: string[]): string {
    const params = new URLSearchParams();
    requestIds.forEach((requestId) => params.append("request_id", requestId));
    return `${API_BASE}/files/output-archive?${params.toString()}`;
  },
};
