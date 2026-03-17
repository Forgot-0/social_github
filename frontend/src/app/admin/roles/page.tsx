"use client";

import { useMemo, useState } from "react";

import {
  useAddRolePermissionsMutation,
  useCreateRoleMutation,
  usePermissionsQuery,
  useRemoveRolePermissionsMutation,
  useRolesQuery,
} from "@/api/hooks";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import type { RoleDTO } from "@/types";

function RoleCard({ role, permissionNames }: { role: RoleDTO; permissionNames: string[] }) {
  const addPerm = useAddRolePermissionsMutation();
  const removePerm = useRemoveRolePermissionsMutation();
  const [perm, setPerm] = useState(permissionNames[0] ?? "");

  return (
    <div className="card">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-lg font-semibold text-gray-900">{role.name}</div>
          <div className="text-sm text-gray-600">{role.description}</div>
          <div className="mt-2">
            <Badge>security_level: {role.security_level}</Badge>
          </div>
        </div>
        <div className="text-sm text-gray-500">ID: {role.id}</div>
      </div>

      <div className="mt-4">
        <div className="text-sm font-semibold text-gray-900">Права роли</div>
        <div className="mt-2 flex flex-wrap gap-2">
          {(role.permissions ?? []).length === 0 ? (
            <span className="text-sm text-gray-500">Нет</span>
          ) : (
            role.permissions?.map((p) => (
              <button
                key={p.id}
                className="rounded-full border border-gray-200 px-3 py-1 text-xs text-gray-700 hover:border-red-200 hover:text-red-700"
                onClick={() => removePerm.mutate({ roleName: role.name, body: { permission: [p.name] } })}
                type="button"
                title="Убрать право"
              >
                {p.name}
              </button>
            ))
          )}
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-2">
          <select value={perm} onChange={(e) => setPerm(e.target.value)} className="input max-w-xs">
            {permissionNames.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
          <button
            className="btn-secondary text-sm"
            type="button"
            onClick={() => perm && addPerm.mutate({ roleName: role.name, body: { permission: [perm] } })}
            disabled={!perm || addPerm.isPending}
          >
            Добавить право
          </button>
        </div>
      </div>
    </div>
  );
}

export default function AdminRolesPage() {
  const [page, setPage] = useState(1);
  const pageSize = 20;
  const roles = useRolesQuery({ page, page_size: pageSize });
  const permissions = usePermissionsQuery({ page: 1, page_size: 500 });
  const createRole = useCreateRoleMutation();

  const permissionNames = useMemo(
    () => permissions.data?.items.map((p) => p.name) ?? [],
    [permissions.data?.items],
  );

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [securityLevel, setSecurityLevel] = useState(1);

  const totalPages = roles.data ? Math.ceil(roles.data.total / pageSize) : 1;

  if (roles.isLoading || permissions.isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Роли</h1>
      <p className="mt-1 text-sm text-gray-600">CRUD ролей и управление правами роли.</p>

      <div className="card mt-6">
        <div className="text-sm font-semibold text-gray-900">Создать роль</div>
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <input value={name} onChange={(e) => setName(e.target.value)} className="input" placeholder="name" />
          <input
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="input"
            placeholder="description"
          />
          <input
            value={securityLevel}
            onChange={(e) => setSecurityLevel(Number(e.target.value))}
            className="input"
            type="number"
            min={0}
            placeholder="security_level"
          />
          <button
            className="btn-primary"
            type="button"
            onClick={() =>
              createRole.mutate({
                name,
                description,
                security_level: securityLevel,
              })
            }
            disabled={!name || !description || createRole.isPending}
          >
            Создать
          </button>
        </div>
      </div>

      <div className="mt-6 grid gap-4">
        {roles.data?.items.map((r) => (
          <RoleCard key={r.id} role={r} permissionNames={permissionNames} />
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

