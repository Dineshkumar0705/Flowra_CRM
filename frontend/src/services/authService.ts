import apiClient from "./apiClient";
import { ApiResponse, LoginResponse, User } from "@/types";

export const authService = {
  async login(
    email: string,
    password: string
  ): Promise<ApiResponse<LoginResponse>> {
    const response = await apiClient.post("/auth/login", { email, password });
    return response.data;
  },

  async signup(
    name: string,
    email: string,
    password: string,
    workspace_name: string
  ): Promise<ApiResponse<LoginResponse>> {
    const response = await apiClient.post("/auth/signup", {
      name,
      email,
      password,
      workspace_name,
    });
    return response.data;
  },

  async refreshToken(refreshToken: string): Promise<ApiResponse<any>> {
    const response = await apiClient.post("/auth/refresh", { refresh_token: refreshToken });
    return response.data;
  },

  async getMe(): Promise<ApiResponse<User>> {
    const response = await apiClient.get("/auth/me");
    return response.data;
  },

  async changePassword(
    current_password: string,
    new_password: string
  ): Promise<ApiResponse<any>> {
    const response = await apiClient.post("/auth/change-password", {
      current_password,
      new_password,
    });
    return response.data;
  },
};
