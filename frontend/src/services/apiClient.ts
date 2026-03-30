import axios, { AxiosInstance, AxiosError } from "axios";
import { useAuthStore } from "@/store/authStore";

const BASE_URL = "http://localhost:8000/api/v1";

const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
});

// Request interceptor - add auth token
apiClient.interceptors.request.use((config) => {
  const store = useAuthStore.getState();
  if (store.accessToken) {
    config.headers.Authorization = `Bearer ${store.accessToken}`;
  }
  return config;
});

// Response interceptor - handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config;
    const store = useAuthStore.getState();

    // If 401 and we have a refresh token, try to refresh
    if (error.response?.status === 401 && store.refreshToken && originalRequest) {
      try {
        const response = await axios.post(
          `${BASE_URL}/auth/refresh`,
          { refresh_token: store.refreshToken },
          { timeout: 10000 }
        );

        const { data } = response.data;
        store.setTokens(data.access_token, store.refreshToken);

        // Retry original request
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        }
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh failed, logout
        store.logout();
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
