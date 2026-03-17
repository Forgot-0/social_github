import { expect, test } from "@playwright/test";

/**
 * E2E-тесты: аутентификация (логин, refresh, защищённые страницы).
 *
 * Для запуска необходим работающий бэкенд на API_URL или мок-сервер.
 * В CI рекомендуется использовать docker-compose с бэкендом.
 */

test.describe("Аутентификация", () => {
  test("показывает форму логина на /login", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("heading", { name: /вход/i })).toBeVisible();
    await expect(page.getByLabel(/имя пользователя/i)).toBeVisible();
    await expect(page.getByLabel(/пароль/i)).toBeVisible();
  });

  test("редирект с /dashboard на /login для неавторизованного пользователя", async ({
    page,
  }) => {
    await page.goto("/dashboard");
    await page.waitForURL(/\/login/);
    expect(page.url()).toContain("/login");
  });

  test("показывает форму регистрации на /register", async ({ page }) => {
    await page.goto("/register");
    await expect(page.getByRole("heading", { name: /регистрация/i })).toBeVisible();
  });

  test("логин с неверными данными показывает ошибку", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel(/имя пользователя/i).fill("wrong_user");
    await page.getByLabel(/пароль/i).fill("wrong_password");
    await page.getByRole("button", { name: /войти/i }).click();

    await expect(page.getByText(/неверное имя пользователя/i)).toBeVisible({ timeout: 5000 });
  });

  /**
   * Полный цикл: логин -> dashboard -> refresh -> logout.
   * Требует реально работающий бэкенд с тестовым пользователем.
   *
   * test("полный цикл авторизации", async ({ page }) => {
   *   await page.goto("/login");
   *   await page.getByLabel(/имя пользователя/i).fill("testuser");
   *   await page.getByLabel(/пароль/i).fill("TestPassword123");
   *   await page.getByRole("button", { name: /войти/i }).click();
   *
   *   await page.waitForURL("/dashboard");
   *   await expect(page.getByText(/добро пожаловать/i)).toBeVisible();
   *
   *   // Проверяем что refresh cookie установлен
   *   const cookies = await page.context().cookies();
   *   const refreshCookie = cookies.find((c) => c.name === "refresh_token");
   *   expect(refreshCookie).toBeTruthy();
   *   expect(refreshCookie?.httpOnly).toBe(true);
   *
   *   // Logout
   *   await page.getByRole("button", { name: /выйти/i }).click();
   *   await page.waitForURL("/login");
   * });
   */
});
