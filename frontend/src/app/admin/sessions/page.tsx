"use client";

import { useState } from "react";

import { useDeleteSessionMutation, useSessionsQuery } from "@/api/hooks";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { formatDateTime } from "@/lib/utils";

export default function AdminSessionsPage() {
  const [page, setPage] = useState(1);
  const pageSize = 30;
  const sessions = useSessionsQuery({ page, page_size: pageSize });
  const del = useDeleteSessionMutation();

  const totalPages = sessions.data ? Math.ceil(sessions.data.total / pageSize) : 1;

  if (sessions.isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Сессии</h1>
      <p className="mt-1 text-sm text-gray-600">Просмотр всех сессий и принудительное завершение.</p>

      <div className="mt-6 grid gap-3">
        {sessions.data?.items.map((s) => (
          <div key={s.id} className="card">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge>session #{s.id}</Badge>
                  <Badge>user #{s.user_id}</Badge>
                  <Badge variant={s.is_active ? "success" : "warning"}>
                    {s.is_active ? "active" : "inactive"}
                  </Badge>
                </div>
                <div className="mt-2 text-sm text-gray-700">{s.device_info}</div>
                <div className="mt-1 text-xs text-gray-500">{s.user_agent}</div>
                <div className="mt-2 text-xs text-gray-400">last_activity: {formatDateTime(s.last_activity)}</div>
              </div>
              <button
                className="btn-secondary text-sm hover:border-red-200 hover:text-red-700"
                type="button"
                onClick={() => del.mutate({ sessionId: s.id })}
                disabled={del.isPending}
              >
                Завершить
              </button>
            </div>
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

