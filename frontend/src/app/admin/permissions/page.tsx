"use client";

import { useState } from "react";

import { useCreatePermissionMutation, useDeletePermissionMutation, usePermissionsQuery } from "@/api/hooks";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";

export default function AdminPermissionsPage() {
  const [page, setPage] = useState(1);
  const pageSize = 50;
  const permissions = usePermissionsQuery({ page, page_size: pageSize });
  const createPerm = useCreatePermissionMutation();
  const deletePerm = useDeletePermissionMutation();
  const [name, setName] = useState("");

  const totalPages = permissions.data ? Math.ceil(permissions.data.total / pageSize) : 1;

  if (permissions.isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Права (permissions)</h1>
      <p className="mt-1 text-sm text-gray-600">Создание и удаление прав.</p>

      <div className="card mt-6">
        <div className="text-sm font-semibold text-gray-900">Создать право</div>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <input value={name} onChange={(e) => setName(e.target.value)} className="input max-w-sm" placeholder="name" />
          <button
            className="btn-primary"
            type="button"
            onClick={() => createPerm.mutate({ name })}
            disabled={!name || createPerm.isPending}
          >
            Создать
          </button>
        </div>
      </div>

      <div className="mt-6 grid gap-3">
        {permissions.data?.items.map((p) => (
          <div key={p.id} className="card flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Badge>#{p.id}</Badge>
              <span className="font-medium text-gray-900">{p.name}</span>
            </div>
            <button
              className="btn-secondary text-sm hover:border-red-200 hover:text-red-700"
              type="button"
              onClick={() => deletePerm.mutate({ name: p.name })}
              disabled={deletePerm.isPending}
            >
              Удалить
            </button>
          </div>
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

