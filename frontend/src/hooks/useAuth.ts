"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import { authService } from "@/services/authService";
import { workspaceService } from "@/services/workspaceService";
import { toast } from "sonner";

export function useAuth() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const { user, workspace, isAuthenticated, setAuth, setTokens, logout: storeLogout } = useAuthStore();

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const response = await authService.login(email, password);
      if (response.success && response.data) {
        const { user, access_token, refresh_token } = response.data;
        // Temporarily set tokens so we can fetch workspace
        setTokens(access_token, refresh_token);
        // Fetch workspace with the new token
        let workspace = null;
        try {
          const wsRes = await workspaceService.getCurrent();
          workspace = wsRes.data;
        } catch (_) {}
        setAuth(user, workspace, access_token, refresh_token);
        toast.success("Welcome back!");
        router.push("/dashboard");
      } else {
        toast.error(response.message || "Login failed");
      }
    } catch (error: any) {
      const message =
        error.response?.data?.message ||
        error.response?.data?.detail ||
        error.message ||
        "Network error — is the backend running?";
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const signup = async (
    name: string,
    email: string,
    password: string,
    workspace_name: string
  ) => {
    setIsLoading(true);
    try {
      const response = await authService.signup(name, email, password, workspace_name);
      if (response.success && response.data) {
        const { user, access_token, refresh_token } = response.data;
        setTokens(access_token, refresh_token);
        // Fetch workspace
        let workspace = null;
        try {
          const wsRes = await workspaceService.getCurrent();
          workspace = wsRes.data;
        } catch (_) {}
        setAuth(user, workspace, access_token, refresh_token);
        toast.success("Account created! Welcome to Flowra 🎉");
        router.push("/dashboard");
      } else {
        toast.error(response.message || "Signup failed");
      }
    } catch (error: any) {
      const message =
        error.response?.data?.message ||
        error.response?.data?.detail ||
        error.message ||
        "Network error — is the backend running?";
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    storeLogout();
    toast.success("Logged out");
    router.push("/login");
  };

  const changePassword = async (currentPassword: string, newPassword: string) => {
    setIsLoading(true);
    try {
      const response = await authService.changePassword(currentPassword, newPassword);
      if (response.success) {
        toast.success("Password changed successfully");
      } else {
        toast.error(response.message || "Failed to change password");
      }
    } catch (error: any) {
      toast.error(error.response?.data?.message || "An error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  return { user, workspace, isAuthenticated, isLoading, login, signup, logout, changePassword };
}
