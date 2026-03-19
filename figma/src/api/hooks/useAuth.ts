/**
 * React Query hooks for Authentication
 */

import { useMutation, UseMutationOptions } from '@tanstack/react-query';
import { authApi } from '../client';
import { tokenManager } from '../tokenManager';
import type {
  AccessTokenResponse,
  LoginRequest,
  SendVerifyCodeRequest,
  VerifyEmailRequest,
  SendResetPasswordCodeRequest,
  ResetPasswordRequest,
  OAuthUrlResponse,
  ApiError,
} from '../types';
import { AxiosError } from 'axios';

/**
 * Login mutation
 * Sets access token in memory on success
 */
export const useLoginMutation = (
  options?: UseMutationOptions<AccessTokenResponse, AxiosError<ApiError>, LoginRequest>
) => {
  return useMutation({
    mutationFn: authApi.login,
    onSuccess: (data) => {
      // Store access token in MEMORY only
      tokenManager.setAccessToken(data.access_token);
    },
    ...options,
  });
};

/**
 * Logout mutation
 * Clears access token from memory on success
 */
export const useLogoutMutation = (
  options?: UseMutationOptions<void, AxiosError<ApiError>, void>
) => {
  return useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      // Clear access token from memory
      tokenManager.clearAccessToken();
    },
    ...options,
  });
};

/**
 * Send verification code mutation
 */
export const useSendVerificationCodeMutation = (
  options?: UseMutationOptions<void, AxiosError<ApiError>, SendVerifyCodeRequest>
) => {
  return useMutation({
    mutationFn: authApi.sendVerificationCode,
    ...options,
  });
};

/**
 * Verify email mutation
 */
export const useVerifyEmailMutation = (
  options?: UseMutationOptions<void, AxiosError<ApiError>, VerifyEmailRequest>
) => {
  return useMutation({
    mutationFn: authApi.verifyEmail,
    ...options,
  });
};

/**
 * Send password reset code mutation
 */
export const useSendPasswordResetCodeMutation = (
  options?: UseMutationOptions<void, AxiosError<ApiError>, SendResetPasswordCodeRequest>
) => {
  return useMutation({
    mutationFn: authApi.sendPasswordResetCode,
    ...options,
  });
};

/**
 * Reset password mutation
 */
export const useResetPasswordMutation = (
  options?: UseMutationOptions<void, AxiosError<ApiError>, ResetPasswordRequest>
) => {
  return useMutation({
    mutationFn: authApi.resetPassword,
    ...options,
  });
};

/**
 * Get OAuth URL mutation
 */
export const useGetOAuthUrlMutation = (
  options?: UseMutationOptions<OAuthUrlResponse, AxiosError<ApiError>, string>
) => {
  return useMutation({
    mutationFn: authApi.getOAuthUrl,
    ...options,
  });
};

/**
 * Get OAuth connect URL mutation
 */
export const useGetOAuthConnectUrlMutation = (
  options?: UseMutationOptions<OAuthUrlResponse, AxiosError<ApiError>, string>
) => {
  return useMutation({
    mutationFn: authApi.getOAuthConnectUrl,
    ...options,
  });
};
