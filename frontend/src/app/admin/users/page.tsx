"use client";

import { useMemo, useState } from "react";

import {
  useAssignRoleMutation,
  useAssignUserPermissionsMutation,
  useRemoveRoleMutation,
  useRemoveUserPermissionsMutation,
  useRolesQuery,
  useUsersQuery,
} from "@/api/hooks";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { filterSystemRoles } from "@/lib/rbac/roles";
import type { UserDTO } from "@/types";

function UserCard({
  user,
  roleNames,
}: {
  user: UserDTO;
  roleNames: string[];
}) {
  const assignRole = useAssignRoleMutation();
  const removeRole = useRemoveRoleMutation();
  const assignPerms = useAssignUserPermissionsMutation();
  const removePerms = useRemoveUserPermissionsMutation();

  const [roleName, setRoleName] = useState(roleNames[0] ?? "");
  const [permName, setPermName] = useState("");

  return (
    <div className="card">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-lg font-semibold text-gray-900">{user.username}</div>
          <div className="text-sm text-gray-600">{user.email}</div>
          <div className="mt-2 flex flex-wrap gap-2">
            <Badge variant={user.is_active ? "success" : "danger"}>
              {user.is_active ? "active" : "inactive"}
            </Badge>
            <Badge variant={user.is_verified ? "success" : "warning"}>
              {user.is_verified ? "verified" : "unverified"}
            </Badge>
          </div>
        </div>
        <div className="text-sm text-gray-500">ID: {user.id}</div>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <div>
          <div className="text-sm font-semibold text-gray-900">Роли</div>
          <div className="mt-2 flex flex-wrap gap-2">
            {(user.roles ?? []).length === 0 ? (
              <span className="text-sm text-gray-500">Нет</span>
            ) : (
              user.roles?.map((r) => (
                <button
                  key={r.id}
                  className="rounded-full border border-gray-200 px-3 py-1 text-xs text-gray-700 hover:border-red-200 hover:text-red-700"
                  onClick={() => removeRole.mutate({ userId: user.id, roleName: r.name })}
                  type="button"
                  title="Снять роль"
                >
                  {r.name}
                </button>
              ))
            )}
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-2">
            <select
              value={roleName}
              onChange={(e) => setRoleName(e.target.value)}
              className="input max-w-xs"
            >
              {roleNames.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
            <button
              className="btn-secondary text-sm"
              type="button"
              onClick={() => roleName && assignRole.mutate({ userId: user.id, body: { role_name: roleName } })}
              disabled={!roleName || assignRole.isPending}
            >
              Назначить роль
            </button>
          </div>
        </div>

        <div>
          <div className="text-sm font-semibold text-gray-900">Персональные права</div>
          <div className="mt-2 flex flex-wrap gap-2">
            {(user.permissions ?? []).length === 0 ? (
              <span className="text-sm text-gray-500">Нет</span>
            ) : (
              user.permissions?.map((p) => (
                <button
                  key={p.id}
                  className="rounded-full border border-gray-200 px-3 py-1 text-xs text-gray-700 hover:border-red-200 hover:text-red-700"
                  onClick={() =>
                    removePerms.mutate({ userId: user.id, body: { permissions: [p.name] } })
                  }
                  type="button"
                  title="Убрать право"
                >
                  {p.name}
                </button>
              ))
            )}
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-2">
            <input
              value={permName}
              onChange={(e) => setPermName(e.target.value)}
              className="input max-w-xs"
              placeholder="permission.name"
            />
            <button
              className="btn-secondary text-sm"
              type="button"
              onClick={() =>
                permName && assignPerms.mutate({ userId: user.id, body: { permissions: [permName] } })
              }
              disabled={!permName || assignPerms.isPending}
            >
              Добавить право
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AdminUsersPage() {
  const [page, setPage] = useState(1);
  const pageSize = 20;
  const users = useUsersQuery({ page, page_size: pageSize });
  const roles = useRolesQuery({ page: 1, page_size: 20 });

  const roleNames = useMemo(
    () => filterSystemRoles(roles.data?.items ?? []).map((r) => r.name),
    [roles.data?.items],
  );
  const totalPages = users.data ? Math.ceil(users.data.total / pageSize) : 1;

  if (users.isLoading || roles.isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Пользователи</h1>
      <p className="mt-1 text-sm text-gray-600">
        Назначение ролей и персональных прав. Клик по роли/праву снимает его.
      </p>

      <div className="mt-6 grid gap-4">
        {users.data?.items.map((u) => (
          <UserCard key={u.id} user={u} roleNames={roleNames} />
        ))}
      </div>

      {totalPages > 1 && (
        <div className="mt-8 flex items-center justify-center gap-2">
          <button
            className="btn-secondary text-sm"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
          >
            Назад
          </button>
          <span className="text-sm text-gray-600">
            {page} / {totalPages}
          </span>
          <button
            className="btn-secondary text-sm"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
          >
            Вперёд
          </button>
        </div>
      )}
    </div>
  );
}

