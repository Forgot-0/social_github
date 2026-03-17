"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { useAuth } from "@/lib/auth/useAuth";

export function Header() {
  const { user, isAuthenticated, logout, hasRole, hasPermission } = useAuth();
  const router = useRouter();

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  return (
    <header className="sticky top-0 z-50 border-b border-gray-200 bg-white/80 backdrop-blur-lg">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-8">
          <Link href="/" className="text-xl font-bold text-brand-600">
            SocialGH
          </Link>
          <nav className="hidden items-center gap-6 md:flex">
            <Link
              href="/positions"
              className="text-sm font-medium text-gray-600 transition-colors hover:text-brand-600"
            >
              Позиции
            </Link>
            {isAuthenticated && (
              <>
                <Link
                  href="/dashboard"
                  className="text-sm font-medium text-gray-600 transition-colors hover:text-brand-600"
                >
                  Панель
                </Link>
                {(hasRole("admin") || hasPermission("admin:*")) && (
                  <Link
                    href="/admin"
                    className="text-sm font-medium text-gray-600 transition-colors hover:text-brand-600"
                  >
                    Админка
                  </Link>
                )}
                <Link
                  href="/projects/new"
                  className="text-sm font-medium text-gray-600 transition-colors hover:text-brand-600"
                >
                  Новый проект
                </Link>
              </>
            )}
          </nav>
        </div>

        <div className="flex items-center gap-4">
          {isAuthenticated ? (
            <>
              <Link
                href="/profile"
                className="text-sm font-medium text-gray-600 transition-colors hover:text-brand-600"
              >
                {user?.username}
              </Link>
              <Link
                href="/settings/sessions"
                className="text-sm text-gray-500 transition-colors hover:text-gray-700"
              >
                Настройки
              </Link>
              <button onClick={handleLogout} className="btn-secondary text-sm">
                Выйти
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="btn-secondary text-sm">
                Войти
              </Link>
              <Link href="/register" className="btn-primary text-sm">
                Регистрация
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
