import apiClient from "./apiClient";
import { ApiResponse, Deal, DealsDashboard } from "@/types";

interface GetDealsParams {
  page?: number;
  page_size?: number;
  stage?: string;
  pipeline_id?: string;
}

interface CreateDealData {
  title: string;
  pipeline_id: string;
  stage_id: string;
  contact_id?: string;
  value?: number;
  priority?: string;
}

export const dealService = {
  async getDeals(params: GetDealsParams = {}): Promise<ApiResponse<Deal[]>> {
    const response = await apiClient.get("/deals", { params });
    return response.data;
  },

  async createDeal(data: CreateDealData): Promise<ApiResponse<Deal>> {
    const response = await apiClient.post("/deals", data);
    return response.data;
  },

  async getDeal(id: string): Promise<ApiResponse<Deal>> {
    const response = await apiClient.get(`/deals/${id}`);
    return response.data;
  },

  async updateDeal(
    id: string,
    data: Partial<CreateDealData>
  ): Promise<ApiResponse<Deal>> {
    const response = await apiClient.patch(`/deals/${id}`, data);
    return response.data;
  },

  async deleteDeal(id: string): Promise<ApiResponse<any>> {
    const response = await apiClient.delete(`/deals/${id}`);
    return response.data;
  },

  async moveDealStage(id: string, stage_id: string): Promise<ApiResponse<Deal>> {
    const response = await apiClient.post(`/deals/${id}/move-stage`, {
      stage_id,
    });
    return response.data;
  },

  async getDashboard(): Promise<ApiResponse<DealsDashboard>> {
    const response = await apiClient.get("/deals/dashboard");
    return response.data;
  },
};
