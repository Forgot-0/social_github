import { expect, test } from "@playwright/test";

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

test.describe("Админка (smoke, mocked API)", () => {
  test("рендерит /admin при admin claims", async ({ page, context }) => {
    await context.addCookies([
      {
        name: "refresh_token",
        value: "test",
        url: "http://localhost:3000",
      },
    ]);

    const accessToken = makeJwt({ roles: ["admin"], permissions: ["admin:*"] });

    // AuthProvider silent refresh
    await page.route("**/api/v1/auth/refresh", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ access_token: accessToken }),
      });
    });

    // /me
    await page.route("**/api/v1/users/me", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ id: 1, username: "admin", email: "admin@example.com" }),
      });
    });

    // Minimal list endpoints for AdminHomePage stats
    const paginated = (items: unknown[], total = items.length) =>
      JSON.stringify({ items, total, page: 1, page_size: 1 });

    await page.route("**/api/v1/users/**", async (route) => {
      // includes /users/ list and also /users/{id}... in other pages (not used here)
      const url = route.request().url();
      if (url.includes("/api/v1/users/") && !url.includes("/api/v1/users/me")) {
        await route.fulfill({ status: 200, contentType: "application/json", body: paginated([]) });
        return;
      }
      await route.fallback();
    });

    await page.route("**/api/v1/roles/**", async (route) => {
      await route.fulfill({ status: 200, contentType: "application/json", body: paginated([]) });
    });
    await page.route("**/api/v1/permissions/**", async (route) => {
      await route.fulfill({ status: 200, contentType: "application/json", body: paginated([]) });
    });
    await page.route("**/api/v1/sessions/**", async (route) => {
      await route.fulfill({ status: 200, contentType: "application/json", body: paginated([]) });
    });
    await page.route("**/api/v1/applications/**", async (route) => {
      await route.fulfill({ status: 200, contentType: "application/json", body: paginated([]) });
    });

    await page.goto("/admin");
    await expect(page.getByRole("heading", { name: "Админ-панель" })).toBeVisible();

    // Can navigate to a sub-page under the same mocked auth
    await page.goto("/admin/users");
    await expect(page.getByRole("heading", { name: "Пользователи" })).toBeVisible();
  });
});

