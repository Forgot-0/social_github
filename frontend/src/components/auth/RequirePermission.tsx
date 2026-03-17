"use client";

import { ReactNode } from "react";

import { AccessDenied } from "@/components/auth/AccessDenied";
import { useAuth } from "@/lib/auth/useAuth";

export function RequirePermission({
  permission,
  children,
  fallback,
}: {
  permission: string;
  children: ReactNode;
  fallback?: ReactNode;
}) {
  const { isLoading, hasPermission } = useAuth();

  if (isLoading) return null;
  if (!hasPermission(permission)) return <>{fallback ?? <AccessDenied />}</>;
  return <>{children}</>;
}

export function RequireAnyPermission({
  permissions,
  children,
  fallback,
}: {
  permissions: string[];
  children: ReactNode;
  fallback?: ReactNode;
}) {
  const { isLoading, hasAnyPermission } = useAuth();

  if (isLoading) return null;
  if (!hasAnyPermission(permissions)) return <>{fallback ?? <AccessDenied />}</>;
  return <>{children}</>;
}

