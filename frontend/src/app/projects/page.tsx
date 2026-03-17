"use client";

import Link from "next/link";
import { useState } from "react";

import { useProjectsQuery } from "@/api/hooks";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { formatDateTime } from "@/lib/utils";

function ProjectsContent() {
  const [page, setPage] = useState(1);
  const pageSize = 18;
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
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Проекты</h1>
          <p className="mt-1 text-gray-600">Смотрите проекты, открывайте детали, создавайте позиции и управляйте заявками.</p>
        </div>
        <Link href="/projects/new" className="btn-primary">
          Создать проект
        </Link>
      </div>

      {projects.data?.items.length === 0 ? (
        <div className="py-16 text-center">
          <p className="text-lg text-gray-500">Пока нет проектов</p>
          <div className="mt-4">
            <Link href="/projects/new" className="btn-primary">
              Создать первый проект
            </Link>
          </div>
        </div>
      ) : (
        <>
          <div className="mt-6 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {projects.data?.items.map((p) => (
              <Link key={p.id} href={`/projects/${p.id}`} className="card block hover:border-brand-200">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="text-lg font-semibold text-gray-900">{p.name}</div>
                  <Badge variant={p.visibility === "public" ? "success" : "warning"}>{p.visibility}</Badge>
                </div>
                <div className="mt-1 text-sm text-gray-500">/{p.slug}</div>
                {p.small_description && <div className="mt-3 text-sm text-gray-700">{p.small_description}</div>}
                <div className="mt-3 flex flex-wrap gap-2">
                  {p.tags.slice(0, 6).map((t) => (
                    <Badge key={t} variant="info">
                      {t}
                    </Badge>
                  ))}
                </div>
                <div className="mt-4 text-xs text-gray-400">
                  updated: {formatDateTime(p.updated_at)}
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

export default function ProjectsPage() {
  return (
    <ProtectedRoute>
      <ProjectsContent />
    </ProtectedRoute>
  );
}

