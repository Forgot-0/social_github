"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useState } from "react";

import { useAuth } from "@/lib/auth/useAuth";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirect = searchParams.get("redirect") ?? "/dashboard";

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await login(username, password);
      router.push(redirect);
    } catch {
      setError("Неверное имя пользователя или пароль");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-10rem)] items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="card">
          <h1 className="mb-6 text-center text-2xl font-bold text-gray-900">Вход в аккаунт</h1>

          {error && (
            <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="username" className="label mb-1">
                Имя пользователя
              </label>
              <input
                id="username"
                type="text"
                className="input"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoComplete="username"
              />
            </div>

            <div>
              <label htmlFor="password" className="label mb-1">
                Пароль
              </label>
              <input
                id="password"
                type="password"
                className="input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </div>

            <button type="submit" className="btn-primary w-full" disabled={isSubmitting}>
              {isSubmitting ? "Вход..." : "Войти"}
            </button>
          </form>

          <div className="mt-4 text-center text-sm text-gray-600">
            Нет аккаунта?{" "}
            <Link href="/register" className="font-medium text-brand-600 hover:text-brand-500">
              Зарегистрироваться
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
