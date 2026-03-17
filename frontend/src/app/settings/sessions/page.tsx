"use client";

import { useDeleteSessionMutation, useUserSessionsQuery } from "@/api/hooks";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { formatDateTime } from "@/lib/utils";

function SessionsContent() {
  const { data: sessions, isLoading } = useUserSessionsQuery();
  const deleteSession = useDeleteSessionMutation();

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="mb-8 text-3xl font-bold text-gray-900">Активные сессии</h1>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <Spinner size="lg" />
        </div>
      ) : !sessions || sessions.length === 0 ? (
        <p className="text-center text-gray-500">Нет активных сессий</p>
      ) : (
        <ul className="space-y-4">
          {sessions.map((session) => (
            <li key={session.id} className="card flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <p className="font-medium text-gray-900">{session.device_info}</p>
                  {session.is_active && <Badge variant="success">Активна</Badge>}
                </div>
                <p className="mt-1 text-sm text-gray-500">{session.user_agent}</p>
                <p className="mt-0.5 text-xs text-gray-400">
                  Последняя активность: {formatDateTime(session.last_activity)}
                </p>
              </div>
              <button
                className="btn-danger text-sm"
                onClick={() => deleteSession.mutate({ sessionId: session.id })}
                disabled={deleteSession.isPending}
              >
                Завершить
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function SessionsPage() {
  return (
    <ProtectedRoute>
      <SessionsContent />
    </ProtectedRoute>
  );
}
