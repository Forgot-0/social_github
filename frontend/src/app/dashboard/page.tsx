"use client";

import Link from "next/link";

import { useApplicationsQuery, usePositionsQuery } from "@/api/hooks";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { useAuth } from "@/lib/auth/useAuth";

function DashboardContent() {
  const { user } = useAuth();
  const positions = usePositionsQuery({ page: 1, page_size: 5 });
  const applications = useApplicationsQuery({ page: 1, page_size: 5 });

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Добро пожаловать, {user?.username}!
        </h1>
        <p className="mt-1 text-gray-600">Обзор вашей активности на платформе</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Последние позиции */}
        <div className="card">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Открытые позиции</h2>
            <Link href="/positions" className="text-sm text-brand-600 hover:text-brand-500">
              Все позиции
            </Link>
          </div>

          {positions.isLoading ? (
            <div className="flex justify-center py-8">
              <Spinner />
            </div>
          ) : positions.data?.items.length === 0 ? (
            <p className="py-8 text-center text-sm text-gray-500">Нет открытых позиций</p>
          ) : (
            <ul className="divide-y divide-gray-100">
              {positions.data?.items.map((pos) => (
                <li key={pos.id} className="py-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-medium text-gray-900">{pos.title}</p>
                      <p className="mt-0.5 text-sm text-gray-500">{pos.description.slice(0, 80)}...</p>
                    </div>
                    <div className="flex gap-2">
                      <Badge variant={pos.is_open ? "success" : "danger"}>
                        {pos.is_open ? "Открыта" : "Закрыта"}
                      </Badge>
                      <Badge>{pos.location_type}</Badge>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Заявки */}
        <div className="card">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Мои заявки</h2>
          </div>

          {applications.isLoading ? (
            <div className="flex justify-center py-8">
              <Spinner />
            </div>
          ) : applications.data?.items.length === 0 ? (
            <p className="py-8 text-center text-sm text-gray-500">Нет заявок</p>
          ) : (
            <ul className="divide-y divide-gray-100">
              {applications.data?.items.map((app) => {
                const statusVariant =
                  app.status === "accepted"
                    ? "success"
                    : app.status === "rejected"
                      ? "danger"
                      : "warning";
                const statusLabel =
                  app.status === "accepted"
                    ? "Принята"
                    : app.status === "rejected"
                      ? "Отклонена"
                      : "Ожидание";

                return (
                  <li key={app.id} className="py-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-500">
                          Проект #{app.project_id} / Позиция #{app.position_id.slice(0, 8)}
                        </p>
                        {app.message && (
                          <p className="mt-0.5 text-sm text-gray-700">{app.message}</p>
                        )}
                      </div>
                      <Badge variant={statusVariant}>{statusLabel}</Badge>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </div>

      <div className="mt-6 flex gap-4">
        <Link href="/projects/new" className="btn-primary">
          Создать проект
        </Link>
        <Link href="/profile" className="btn-secondary">
          Мой профиль
        </Link>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <DashboardContent />
    </ProtectedRoute>
  );
}
