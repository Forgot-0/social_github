"use client";

import { ReactNode } from "react";

import { AccessDenied } from "@/components/auth/AccessDenied";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { useAuth } from "@/lib/auth/useAuth";

const DEFAULT_ADMIN_PERMISSIONS = [
  "admin:*",
  "rbac:*",
  "users:*",
  "roles:*",
  "permissions:*",
  "sessions:*",
  "applications:*",
  "projects:*",
  "positions:*",
];

export function AdminRoute({
  children,
  fallback,
  permissions = DEFAULT_ADMIN_PERMISSIONS,
}: {
  children: ReactNode;
  fallback?: ReactNode;
  permissions?: string[];
}) {
  const { isLoading, isAuthenticated, hasRole, hasAnyPermission } = useAuth();

  return (
    <ProtectedRoute>
      {isLoading ? null : !isAuthenticated ? null : hasRole("admin") || hasAnyPermission(permissions) ? (
        <>{children}</>
      ) : (
        <>{fallback ?? <AccessDenied />}</>
      )}
    </ProtectedRoute>
  );
}

