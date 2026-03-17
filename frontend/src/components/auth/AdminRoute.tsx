"use client";

import { ReactNode } from "react";

import { AccessDenied } from "@/components/auth/AccessDenied";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { useAuth } from "@/lib/auth/useAuth";

export function AdminRoute({
  children,
  fallback,
}: {
  children: ReactNode;
  fallback?: ReactNode;
}) {
  const { isLoading, isAuthenticated, hasRole } = useAuth();

  return (
    <ProtectedRoute>
      {isLoading ? null : !isAuthenticated ? null : hasRole("super_admin") || hasRole("system_admin") ? (
        <>{children}</>
      ) : (
        <>{fallback ?? <AccessDenied />}</>
      )}
    </ProtectedRoute>
  );
}

