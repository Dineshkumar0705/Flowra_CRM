"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import apiClient from "@/services/apiClient";
import { AxiosRequestConfig } from "axios";

export function useApi<T>(
  url: string,
  options?: AxiosRequestConfig,
  queryOptions?: any
) {
  return useQuery({
    queryKey: [url],
    queryFn: async () => {
      const response = await apiClient.get(url, options);
      return response.data;
    },
    ...queryOptions,
  });
}

export function useApiMutation<T, E = any>(
  method: "post" | "patch" | "put" | "delete" = "post",
  options?: any
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ url, data }: { url: string; data?: any }) => {
      const response = await apiClient[method](url, data);
      return response.data;
    },
    ...options,
  });
}
