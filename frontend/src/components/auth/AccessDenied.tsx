"use client";

import Link from "next/link";
import { ReactNode } from "react";

export function AccessDenied({
  title = "Доступ запрещён",
  description = "У вас нет прав для просмотра этой страницы.",
  action,
}: {
  title?: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="mx-auto max-w-2xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="card">
        <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
        <p className="mt-2 text-gray-600">{description}</p>
        <div className="mt-6 flex flex-wrap gap-3">
          {action ?? (
            <>
              <Link href="/dashboard" className="btn-primary">
                На панель
              </Link>
              <Link href="/" className="btn-secondary">
                На главную
              </Link>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

