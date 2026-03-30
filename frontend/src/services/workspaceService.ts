import apiClient from "./apiClient";
import { ApiResponse, Workspace } from "@/types";

export const workspaceService = {
  async getCurrent(): Promise<ApiResponse<Workspace>> {
    const response = await apiClient.get("/workspaces/current");
    return response.data;
  },
  async update(data: { name?: string }): Promise<ApiResponse<Workspace>> {
    const response = await apiClient.patch("/workspaces/current", data);
    return response.data;
  },
  async getMembers(): Promise<ApiResponse<any[]>> {
    const response = await apiClient.get("/workspaces/current/members");
    return response.data;
  },
};
