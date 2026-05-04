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
