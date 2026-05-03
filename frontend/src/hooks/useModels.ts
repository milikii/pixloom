"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export function useModels() {
  return useQuery({
    queryKey: ["models"],
    queryFn: () => apiClient.getModels(),
    staleTime: 30_000,
  });
}

export function useModelGuidance(modelId: string | null) {
  return useQuery({
    queryKey: ["model-guidance", modelId],
    queryFn: () => apiClient.getModelGuidance(modelId!),
    enabled: !!modelId,
    staleTime: 60_000,
  });
}
