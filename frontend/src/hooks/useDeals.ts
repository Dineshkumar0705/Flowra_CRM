"use client";

import { useQuery } from "@tanstack/react-query";
import { dealService } from "@/services/dealService";

export function useDeals(pipelineId?: string) {
  return useQuery({
    queryKey: ["deals", { pipelineId }],
    queryFn: async () => {
      const response = await dealService.getDeals({
        page_size: 100,
        pipeline_id: pipelineId,
      });
      return response.data;
    },
    enabled: !!pipelineId,
  });
}

export function useDealDashboard() {
  return useQuery({
    queryKey: ["deals", "dashboard"],
    queryFn: async () => {
      const response = await dealService.getDashboard();
      return response.data;
    },
  });
}
