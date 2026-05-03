"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { BatchCreateRequest } from "@/lib/types";

export function useFileUpload() {
  return useMutation({
    mutationFn: (files: File[]) => apiClient.uploadFiles(files),
  });
}

export function useSubmitBatch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: BatchCreateRequest) => apiClient.createBatch(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
    },
  });
}
