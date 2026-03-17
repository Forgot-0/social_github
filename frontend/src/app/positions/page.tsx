"use client";

import Link from "next/link";
import { useState } from "react";

import { usePositionsQuery } from "@/api/hooks";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";

export default function PositionsPage() {
  const [page, setPage] = useState(1);
  const pageSize = 12;
  const { data, isLoading } = usePositionsQuery({ page, page_size: pageSize });

  const totalPages = data ? Math.ceil(data.total / pageSize) : 1;

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="mb-8 text-3xl font-bold text-gray-900">Открытые позиции</h1>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <Spinner size="lg" />
        </div>
      ) : data?.items.length === 0 ? (
        <div className="py-16 text-center">
          <p className="text-lg text-gray-500">Пока нет открытых позиций</p>
        </div>
      ) : (
        <>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {data?.items.map((pos) => (
              <Link
                key={pos.id}
                href={`/positions/${pos.id}`}
                className="card flex flex-col hover:border-brand-200"
              >
                <div className="mb-3 flex items-start justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">{pos.title}</h3>
                  <Badge variant={pos.is_open ? "success" : "danger"}>
                    {pos.is_open ? "Открыта" : "Закрыта"}
                  </Badge>
                </div>
                <p className="mb-4 flex-1 text-sm text-gray-600">{pos.description}</p>

                <div className="mb-3 flex flex-wrap gap-1.5">
                  {pos.required_skills.map((skill) => (
                    <Badge key={skill} variant="info">
                      {skill}
                    </Badge>
                  ))}
                </div>

                <div className="flex items-center gap-3 text-xs text-gray-500">
                  <span>{pos.location_type}</span>
                  <span>&middot;</span>
                  <span>Нагрузка: {pos.expected_load}</span>
                </div>
              </Link>
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
        </>
      )}
    </div>
  );
}
