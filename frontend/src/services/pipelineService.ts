import apiClient from "./apiClient";
import { ApiResponse, Pipeline, Stage } from "@/types";

interface PipelineBoardResponse {
  stages: Array<
    Stage & {
      deals: any[];
    }
  >;
}

interface CreatePipelineData {
  name: string;
  description?: string;
}

export const pipelineService = {
  async getPipelines(): Promise<ApiResponse<Pipeline[]>> {
    const response = await apiClient.get("/pipelines");
    return response.data;
  },

  async getPipeline(id: string): Promise<ApiResponse<Pipeline>> {
    const response = await apiClient.get(`/pipelines/${id}`);
    return response.data;
  },

  async createPipeline(data: CreatePipelineData): Promise<ApiResponse<Pipeline>> {
    const response = await apiClient.post("/pipelines", data);
    return response.data;
  },

  async getPipelineBoard(
    pipelineId: string
  ): Promise<ApiResponse<PipelineBoardResponse>> {
    const response = await apiClient.get(`/pipelines/${pipelineId}/board`);
    return response.data;
  },
};
