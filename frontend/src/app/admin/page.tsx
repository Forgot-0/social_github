"use client";

import Link from "next/link";

import { useApplicationsQuery, usePermissionsQuery, useRolesQuery, useSessionsQuery, useUsersQuery } from "@/api/hooks";
import { Spinner } from "@/components/ui/Spinner";

function Stat({ label, value, href }: { label: string; value: number | string; href: string }) {
  return (
    <Link href={href} className="card block hover:border-brand-200">
      <div className="text-sm text-gray-500">{label}</div>
      <div className="mt-1 text-2xl font-bold text-gray-900">{value}</div>
    </Link>
  );
}

export default function AdminHomePage() {
  const users = useUsersQuery({ page: 1, page_size: 1 });
  const roles = useRolesQuery({ page: 1, page_size: 1 });
  const permissions = usePermissionsQuery({ page: 1, page_size: 1 });
  const sessions = useSessionsQuery({ page: 1, page_size: 1 });
  const applications = useApplicationsQuery({ page: 1, page_size: 1 });

  if (users.isLoading || roles.isLoading || permissions.isLoading || sessions.isLoading || applications.isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900">Админ-панель</h1>
      <p className="mt-1 text-gray-600">RBAC и модерация доменных сущностей</p>

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Пользователи" value={users.data?.total ?? "—"} href="/admin/users" />
        <Stat label="Роли" value={roles.data?.total ?? "—"} href="/admin/roles" />
        <Stat label="Права" value={permissions.data?.total ?? "—"} href="/admin/permissions" />
        <Stat label="Сессии" value={sessions.data?.total ?? "—"} href="/admin/sessions" />
        <Stat label="Заявки" value={applications.data?.total ?? "—"} href="/admin/applications" />
      </div>
    </div>
  );
}

