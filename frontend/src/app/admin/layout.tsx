"use client";

import Link from "next/link";
import { ReactNode } from "react";

import { AdminRoute } from "@/components/auth/AdminRoute";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/admin", label: "Обзор" },
  { href: "/admin/users", label: "Пользователи" },
  { href: "/admin/roles", label: "Роли" },
  { href: "/admin/permissions", label: "Права" },
  { href: "/admin/sessions", label: "Сессии" },
  { href: "/admin/applications", label: "Заявки" },
  { href: "/admin/projects", label: "Проекты" },
  { href: "/admin/positions", label: "Позиции" },
];

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <AdminRoute>
      <div className="mx-auto grid max-w-7xl grid-cols-1 gap-6 px-4 py-8 sm:px-6 lg:grid-cols-[240px_1fr] lg:px-8">
        <aside className="card h-fit p-3">
          <div className="px-2 pb-2 text-sm font-semibold text-gray-900">Админка</div>
          <nav className="flex flex-col gap-1">
            {NAV.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "rounded-md px-2 py-1.5 text-sm text-gray-700 hover:bg-gray-50 hover:text-brand-700",
                )}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </aside>
        <section>{children}</section>
      </div>
    </AdminRoute>
  );
}

