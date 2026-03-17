"use client";

import Link from "next/link";
import { useState } from "react";

import { useProjectsQuery } from "@/api/hooks";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { formatDateTime } from "@/lib/utils";

export default function AdminProjectsPage() {
  const [page, setPage] = useState(1);
  const pageSize = 20;
  const projects = useProjectsQuery({ page, page_size: pageSize });

  const totalPages = projects.data ? Math.ceil(projects.data.total / pageSize) : 1;

  if (projects.isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Проекты</h1>
      <p className="mt-1 text-sm text-gray-600">Список проектов (просмотр и переход в детали).</p>

      <div className="mt-6 grid gap-3">
        {projects.data?.items.map((p) => (
          <div key={p.id} className="card flex flex-wrap items-start justify-between gap-3">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <Link href={`/projects/${p.id}`} className="text-lg font-semibold text-brand-700 hover:underline">
                  {p.name}
                </Link>
                <Badge>#{p.id}</Badge>
                <Badge variant={p.visibility === "public" ? "success" : "warning"}>{p.visibility}</Badge>
              </div>
              {p.small_description && <div className="mt-1 text-sm text-gray-600">{p.small_description}</div>}
              <div className="mt-2 flex flex-wrap gap-2">
                {p.tags.slice(0, 8).map((t) => (
                  <Badge key={t} variant="info">
                    {t}
                  </Badge>
                ))}
              </div>
              <div className="mt-2 text-xs text-gray-400">
                owner: {p.owner_id} · created: {formatDateTime(p.created_at)} · updated: {formatDateTime(p.updated_at)}
              </div>
            </div>
            <Link href={`/projects/${p.id}`} className="btn-secondary text-sm">
              Открыть
            </Link>
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

