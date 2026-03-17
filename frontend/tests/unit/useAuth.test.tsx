import { renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AuthContext, AuthContextValue } from "@/lib/auth/AuthProvider";
import { useAuth } from "@/lib/auth/useAuth";

const mockValue: AuthContextValue = {
  user: { id: 1, username: "test", email: "test@example.com" },
  isAuthenticated: true,
  isLoading: false,
  login: async () => {},
  logout: async () => {},
  refreshAuth: async () => {},
};

describe("useAuth", () => {
  it("should return context value when inside AuthProvider", () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthContext.Provider value={mockValue}>{children}</AuthContext.Provider>
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user?.username).toBe("test");
  });

  it("should throw when used outside AuthProvider", () => {
    expect(() => {
      renderHook(() => useAuth());
    }).toThrow("useAuth must be used within <AuthProvider>");
  });
});
