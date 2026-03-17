"use client";

import Link from "next/link";
import { useState } from "react";

import { useProfilesQuery } from "@/api/hooks";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";

function ProfilesContent() {
  const [page, setPage] = useState(1);
  const pageSize = 18;
  const profiles = useProfilesQuery({ page, page_size: pageSize });

  const totalPages = profiles.data ? Math.ceil(profiles.data.total / pageSize) : 1;

  if (profiles.isLoading) {
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
          <h1 className="text-3xl font-bold text-gray-900">Профили</h1>
          <p className="mt-1 text-gray-600">Смотрите профили и приглашайте понравившихся кандидатов в свой проект.</p>
        </div>
        <Link href="/projects" className="btn-secondary">
          Мои проекты
        </Link>
      </div>

      {profiles.data?.items.length === 0 ? (
        <div className="py-16 text-center">
          <p className="text-lg text-gray-500">Пока нет профилей</p>
        </div>
      ) : (
        <>
          <div className="mt-6 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {profiles.data?.items.map((p) => (
              <Link key={p.id} href={`/profiles/${p.id}`} className="card block hover:border-brand-200">
                <div className="flex items-start justify-between gap-2">
                  <div className="text-lg font-semibold text-gray-900">{p.display_name ?? `Профиль #${p.id}`}</div>
                  <Badge>#{p.id}</Badge>
                </div>
                {p.specialization && <div className="mt-1 text-sm text-gray-600">{p.specialization}</div>}
                {p.bio && <div className="mt-3 text-sm text-gray-700">{p.bio.slice(0, 140)}{p.bio.length > 140 ? "..." : ""}</div>}
                <div className="mt-3 flex flex-wrap gap-2">
                  {p.skills.slice(0, 8).map((s) => (
                    <Badge key={s} variant="info">
                      {s}
                    </Badge>
                  ))}
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

export default function ProfilesPage() {
  return (
    <ProtectedRoute>
      <ProfilesContent />
    </ProtectedRoute>
  );
}

