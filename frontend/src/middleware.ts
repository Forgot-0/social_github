import { NextRequest, NextResponse } from "next/server";

const PROTECTED_PATHS = ["/dashboard", "/profile", "/settings", "/projects"];
const AUTH_PATHS = ["/login", "/register"];

/**
 * Next.js Edge Middleware.
 *
 * Проверяем наличие refresh_token cookie (HttpOnly, Secure, SameSite=strict).
 * Middleware НЕ читает значение cookie — только проверяет его существование,
 * что безопасно для Edge Runtime.
 *
 * Реальная валидация токена всегда происходит на бэкенде.
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const hasRefreshToken = request.cookies.has("refresh_token");

  const isProtected = PROTECTED_PATHS.some(
    (p) => pathname === p || pathname.startsWith(p + "/"),
  );
  const isAuthPage = AUTH_PATHS.some((p) => pathname === p || pathname.startsWith(p + "/"));

  if (isProtected && !hasRefreshToken) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  if (isAuthPage && hasRefreshToken) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/profile/:path*",
    "/settings/:path*",
    "/projects/:path*",
    "/login",
    "/register",
  ],
};
