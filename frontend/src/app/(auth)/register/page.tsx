"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { useRegisterMutation } from "@/api/hooks";

export default function RegisterPage() {
  const router = useRouter();
  const register = useRegisterMutation();

  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    password_repeat: "",
  });
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    if (form.password !== form.password_repeat) {
      setError("Пароли не совпадают");
      return;
    }

    try {
      await register.mutateAsync(form);
      router.push("/login");
    } catch {
      setError("Ошибка регистрации. Возможно, пользователь с таким именем или email уже существует.");
    }
  };

  const updateField = (field: string, value: string) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  return (
    <div className="flex min-h-[calc(100vh-10rem)] items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="card">
          <h1 className="mb-6 text-center text-2xl font-bold text-gray-900">Регистрация</h1>

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
                value={form.username}
                onChange={(e) => updateField("username", e.target.value)}
                required
                minLength={4}
                maxLength={100}
              />
            </div>

            <div>
              <label htmlFor="email" className="label mb-1">
                Email
              </label>
              <input
                id="email"
                type="email"
                className="input"
                value={form.email}
                onChange={(e) => updateField("email", e.target.value)}
                required
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
                value={form.password}
                onChange={(e) => updateField("password", e.target.value)}
                required
                minLength={8}
              />
            </div>

            <div>
              <label htmlFor="password_repeat" className="label mb-1">
                Повторите пароль
              </label>
              <input
                id="password_repeat"
                type="password"
                className="input"
                value={form.password_repeat}
                onChange={(e) => updateField("password_repeat", e.target.value)}
                required
              />
            </div>

            <button type="submit" className="btn-primary w-full" disabled={register.isPending}>
              {register.isPending ? "Регистрация..." : "Зарегистрироваться"}
            </button>
          </form>

          <div className="mt-4 text-center text-sm text-gray-600">
            Уже есть аккаунт?{" "}
            <Link href="/login" className="font-medium text-brand-600 hover:text-brand-500">
              Войти
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
