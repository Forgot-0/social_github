import type { SessionDTO } from '../../../types/api/session.ts';

type SessionsListProps = {
  isLoading: boolean;
  error: string | null;
  sessions: SessionDTO[];
  pendingId: number | null;
  onTerminate: (sessionId: number) => void;
};

export function SessionsList({
  isLoading,
  error,
  sessions,
  pendingId,
  onTerminate,
}: SessionsListProps) {
  if (isLoading) {
    return <p className="mt-4 text-sm text-zinc-500">Загрузка сессий...</p>;
  }

  if (error) {
    return <p className="mt-4 text-sm text-red-300">{error}</p>;
  }

  if (!sessions.length) {
    return (
      <p className="mt-4 text-sm text-zinc-500">Активные сессии не найдены.</p>
    );
  }

  return (
    <div className="mt-4 space-y-3">
      {sessions.map((session) => (
        <div
          key={session.id}
          className="rounded-xl border border-zinc-800 bg-zinc-950 p-4"
        >
          <p className="text-sm text-zinc-200">
            {session.device_info || 'Unknown device'}
          </p>
          <p className="mt-1 text-xs text-zinc-500">{session.user_agent}</p>
          <p className="mt-1 text-xs text-zinc-500">
            Последняя активность:{' '}
            {new Date(session.last_activity).toLocaleString()}
          </p>
          <div className="mt-3 flex items-center justify-between">
            <span className="text-xs text-zinc-500">
              Статус: {session.is_active ? 'Активна' : 'Завершена'}
            </span>
            <button
              type="button"
              onClick={() => onTerminate(session.id)}
              disabled={!session.is_active || pendingId === session.id}
              className="rounded-lg border border-red-900/60 px-3 py-1.5 text-xs text-red-200 hover:bg-red-950/40 disabled:opacity-50"
            >
              {pendingId === session.id ? 'Завершение...' : 'Завершить сессию'}
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
