"use client";

import { useQuery } from "@tanstack/react-query";
import { pipelineService } from "@/services/pipelineService";

export function usePipelines() {
  return useQuery({
    queryKey: ["pipelines"],
    queryFn: async () => {
      const response = await pipelineService.getPipelines();
      return response.data;
    },
  });
}

export function usePipelineBoard(pipelineId: string) {
  return useQuery({
    queryKey: ["pipeline-board", pipelineId],
    queryFn: async () => {
      const response = await pipelineService.getPipelineBoard(pipelineId);
      return response.data;
    },
    enabled: !!pipelineId,
  });
}
