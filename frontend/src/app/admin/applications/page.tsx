"use client";

import { useState } from "react";

import { useApplicationsQuery, useApproveApplicationMutation, useRejectApplicationMutation } from "@/api/hooks";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import type { ApplicationDTO } from "@/types";

function StatusBadge({ status }: { status: ApplicationDTO["status"] }) {
  const variant = status === "accepted" ? "success" : status === "rejected" ? "danger" : "warning";
  return <Badge variant={variant}>{String(status)}</Badge>;
}

export default function AdminApplicationsPage() {
  const [page, setPage] = useState(1);
  const pageSize = 30;
  const apps = useApplicationsQuery({ page, page_size: pageSize });
  const approve = useApproveApplicationMutation();
  const reject = useRejectApplicationMutation();

  const totalPages = apps.data ? Math.ceil(apps.data.total / pageSize) : 1;

  if (apps.isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Заявки</h1>
      <p className="mt-1 text-sm text-gray-600">Approve/Reject заявок на позиции.</p>

      <div className="mt-6 grid gap-3">
        {apps.data?.items.map((a) => (
          <div key={a.id} className="card">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge>app #{a.id.slice(0, 8)}</Badge>
                  <Badge>project #{a.project_id}</Badge>
                  <Badge>position #{a.position_id.slice(0, 8)}</Badge>
                  <Badge>candidate #{a.candidate_id}</Badge>
                  <StatusBadge status={a.status} />
                </div>
                {a.message && <div className="mt-2 text-sm text-gray-700">{a.message}</div>}
              </div>

              {a.status === "pending" ? (
                <div className="flex gap-2">
                  <button
                    className="btn-primary text-sm"
                    type="button"
                    onClick={() => approve.mutate({ applicationId: a.id })}
                    disabled={approve.isPending}
                  >
                    Approve
                  </button>
                  <button
                    className="btn-secondary text-sm hover:border-red-200 hover:text-red-700"
                    type="button"
                    onClick={() => reject.mutate({ applicationId: a.id })}
                    disabled={reject.isPending}
                  >
                    Reject
                  </button>
                </div>
              ) : (
                <div className="text-sm text-gray-500">
                  decided_by: {a.decided_by ?? "—"}
                </div>
              )}
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

