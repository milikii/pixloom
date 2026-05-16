"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export function useStorage() {
  return useQuery({
    queryKey: ["storage"],
    queryFn: () => apiClient.getStorage(),
    refetchInterval: 30_000,
    staleTime: 10_000,
  });
}
