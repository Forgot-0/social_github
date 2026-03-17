import { describe, expect, it, beforeEach } from "vitest";

import { tokenManager } from "@/lib/auth/token-manager";

describe("tokenManager", () => {
  beforeEach(() => {
    tokenManager.clearToken();
  });

  it("should return null when no token is set", () => {
    expect(tokenManager.getToken()).toBeNull();
  });

  it("should store and retrieve a token", () => {
    tokenManager.setToken("test-access-token");
    expect(tokenManager.getToken()).toBe("test-access-token");
  });

  it("should clear the token", () => {
    tokenManager.setToken("test-token");
    tokenManager.clearToken();
    expect(tokenManager.getToken()).toBeNull();
  });

  it("should overwrite previously set token", () => {
    tokenManager.setToken("old-token");
    tokenManager.setToken("new-token");
    expect(tokenManager.getToken()).toBe("new-token");
  });
});
