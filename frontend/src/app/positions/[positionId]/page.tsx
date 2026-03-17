"use client";

import { useParams } from "next/navigation";
import { useState } from "react";

import { useApplyToPositionMutation, usePositionQuery } from "@/api/hooks";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";

function PositionDetailContent() {
  const params = useParams();
  const positionId = String(params.positionId ?? "");
  const position = usePositionQuery(positionId);
  const apply = useApplyToPositionMutation();
  const [message, setMessage] = useState("");

  if (position.isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!position.data) {
    return (
      <div className="py-16 text-center">
        <p className="text-lg text-gray-500">Позиция не найдена</p>
      </div>
    );
  }

  const p = position.data;

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{p.title}</h1>
            <p className="mt-1 text-sm text-gray-600">Project #{p.project_id}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge variant={p.is_open ? "success" : "danger"}>{p.is_open ? "Открыта" : "Закрыта"}</Badge>
            <Badge>{p.location_type}</Badge>
            <Badge>{p.expected_load}</Badge>
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900">Описание</h2>
        <p className="mt-2 whitespace-pre-wrap text-gray-700">{p.description}</p>

        {p.responsibilities && (
          <>
            <h3 className="mt-6 text-sm font-semibold text-gray-900">Обязанности</h3>
            <p className="mt-2 whitespace-pre-wrap text-gray-700">{p.responsibilities}</p>
          </>
        )}

        <h3 className="mt-6 text-sm font-semibold text-gray-900">Навыки</h3>
        <div className="mt-2 flex flex-wrap gap-2">
          {p.required_skills.map((s) => (
            <Badge key={s} variant="info">
              {s}
            </Badge>
          ))}
        </div>
      </div>

      <div className="card mt-6">
        <h2 className="text-lg font-semibold text-gray-900">Отклик</h2>
        <p className="mt-1 text-sm text-gray-600">Короткое сообщение команде (опционально).</p>
        <textarea
          className="input mt-3 min-h-28 w-full"
          placeholder="Сообщение…"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />
        <div className="mt-3 flex gap-2">
          <button
            className="btn-primary"
            type="button"
            onClick={() => apply.mutate({ positionId, body: { message: message || null } })}
            disabled={!p.is_open || apply.isPending}
          >
            Откликнуться
          </button>
          {!p.is_open && <span className="text-sm text-gray-500">Позиция закрыта</span>}
        </div>
      </div>
    </div>
  );
}

export default function PositionDetailPage() {
  return (
    <ProtectedRoute>
      <PositionDetailContent />
    </ProtectedRoute>
  );
}

