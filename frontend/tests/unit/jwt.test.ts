import { describe, expect, it } from "vitest";

import { decodeJwtPayload, extractAuthClaims } from "@/lib/auth/jwt";

function b64url(input: string): string {
  return Buffer.from(input, "utf-8")
    .toString("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/g, "");
}

function makeJwt(payload: Record<string, unknown>): string {
  const header = b64url(JSON.stringify({ alg: "none", typ: "JWT" }));
  const body = b64url(JSON.stringify(payload));
  return `${header}.${body}.`;
}

describe("jwt claims", () => {
  it("decodes payload and extracts roles/permissions arrays", () => {
    const token = makeJwt({ roles: ["admin"], permissions: ["admin:*", "users:read"] });
    const payload = decodeJwtPayload(token);
    const claims = extractAuthClaims(payload);
    expect(claims.roles).toEqual(["admin"]);
    expect(claims.permissions).toEqual(["admin:*", "users:read"]);
  });

  it("extracts permissions from scope string", () => {
    const token = makeJwt({ scope: "admin:* users:read" });
    const claims = extractAuthClaims(decodeJwtPayload(token));
    expect(claims.permissions).toEqual(["admin:*", "users:read"]);
  });

  it("returns empty claims on invalid token", () => {
    const claims = extractAuthClaims(decodeJwtPayload("not-a-jwt"));
    expect(claims.roles).toEqual([]);
    expect(claims.permissions).toEqual([]);
  });
});

