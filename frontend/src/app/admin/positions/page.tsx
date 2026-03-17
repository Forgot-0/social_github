"use client";

import { useState } from "react";

import { useDeletePositionMutation, usePositionsQuery } from "@/api/hooks";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";

export default function AdminPositionsPage() {
  const [page, setPage] = useState(1);
  const pageSize = 30;
  const positions = usePositionsQuery({ page, page_size: pageSize });
  const del = useDeletePositionMutation();

  const totalPages = positions.data ? Math.ceil(positions.data.total / pageSize) : 1;

  if (positions.isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Позиции</h1>
      <p className="mt-1 text-sm text-gray-600">Список позиций и базовые действия (удаление).</p>

      <div className="mt-6 grid gap-3">
        {positions.data?.items.map((p) => (
          <div key={p.id} className="card">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-lg font-semibold text-gray-900">{p.title}</span>
                  <Badge>#{p.id.slice(0, 8)}</Badge>
                  <Badge>project #{p.project_id}</Badge>
                  <Badge variant={p.is_open ? "success" : "danger"}>{p.is_open ? "open" : "closed"}</Badge>
                  <Badge>{p.location_type}</Badge>
                  <Badge>{p.expected_load}</Badge>
                </div>
                <div className="mt-2 text-sm text-gray-600">{p.description}</div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {p.required_skills.slice(0, 10).map((s) => (
                    <Badge key={s} variant="info">
                      {s}
                    </Badge>
                  ))}
                </div>
              </div>
              <button
                className="btn-secondary text-sm hover:border-red-200 hover:text-red-700"
                type="button"
                onClick={() => del.mutate({ positionId: p.id })}
                disabled={del.isPending}
              >
                Удалить
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

