"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/api/client";
import { tokenManager } from "@/lib/auth/token-manager";
import type {
  AccessTokenResponse,
  ResetPasswordRequest,
  SendResetPasswordCodeRequest,
  SendVerifyCodeRequest,
  VerifyEmailRequest,
} from "@/types";

export function useLoginMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ username, password }: { username: string; password: string }) => {
      const formData = new URLSearchParams();
      formData.append("username", username);
      formData.append("password", password);

      const { data } = await apiClient.post<AccessTokenResponse>("/v1/auth/login", formData, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });
      tokenManager.setToken(data.access_token);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["currentUser"] });
    },
  });
}

export function useLogoutMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      await apiClient.post("/v1/auth/logout");
    },
    onSettled: () => {
      tokenManager.clearToken();
      queryClient.clear();
    },
  });
}

export function useRefreshMutation() {
  return useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.post<AccessTokenResponse>("/v1/auth/refresh");
      tokenManager.setToken(data.access_token);
      return data;
    },
  });
}

export function useSendVerifyCodeMutation() {
  return useMutation({
    mutationFn: async (body: SendVerifyCodeRequest) => {
      await apiClient.post("/v1/auth/verifications/email", body);
    },
  });
}

export function useVerifyEmailMutation() {
  return useMutation({
    mutationFn: async (body: VerifyEmailRequest) => {
      await apiClient.post("/v1/auth/verifications/email/verify", body);
    },
  });
}

export function useSendResetPasswordCodeMutation() {
  return useMutation({
    mutationFn: async (body: SendResetPasswordCodeRequest) => {
      await apiClient.post("/v1/auth/password-resets", body);
    },
  });
}

export function useResetPasswordMutation() {
  return useMutation({
    mutationFn: async (body: ResetPasswordRequest) => {
      await apiClient.post("/v1/auth/password-resets/confirm", body);
    },
  });
}
