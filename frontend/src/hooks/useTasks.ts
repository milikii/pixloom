"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export function useTasks(limit = 60) {
  return useQuery({
    queryKey: ["tasks", limit],
    queryFn: () => apiClient.getTasks(limit),
    refetchInterval: 3_000,
    staleTime: 2_000,
  });
}

export function useTaskDelete() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (requestId: string) => apiClient.deleteTask(requestId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
    },
  });
}

export function useRequestLog(requestId: string | null) {
  return useQuery({
    queryKey: ["logs", requestId],
    queryFn: () => apiClient.getRequestLog(requestId!),
    enabled: !!requestId,
  });
}
