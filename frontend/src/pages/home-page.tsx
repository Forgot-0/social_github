import { Navigate, useNavigate } from 'react-router';
import { useAuth } from '../features/auth/auth-context.tsx';

export function HomePage() {
  const navigate = useNavigate();
  const { isReady, isAuthenticated, user, logout } = useAuth();

  if (!isReady) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-zinc-950 text-zinc-400">
        Загрузка…
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen bg-zinc-950 px-4 py-12 text-zinc-100">
      <div className="mx-auto max-w-lg rounded-2xl border border-zinc-800 bg-zinc-900/80 p-8">
        <h1 className="text-2xl font-semibold">Вы вошли</h1>
        <p className="mt-2 text-zinc-400">
          Сессия: access token в памяти; обновление через httpOnly cookie{' '}
          <code className="rounded bg-zinc-800 px-1 text-sm">
            refresh_token
          </code>{' '}
          (SameSite=strict, Secure).
        </p>
        {user ? (
          <ul className="mt-6 space-y-1 text-sm text-zinc-300">
            <li>
              <span className="text-zinc-500">ID:</span> {user.id}
            </li>
            <li>
              <span className="text-zinc-500">Логин:</span> {user.username}
            </li>
            <li>
              <span className="text-zinc-500">Email:</span> {user.email}
            </li>
          </ul>
        ) : null}
        <button
          type="button"
          onClick={() => void logout().then(() => navigate('/login'))}
          className="mt-8 rounded-lg border border-zinc-600 px-4 py-2 text-sm hover:bg-zinc-800"
        >
          Выйти
        </button>
      </div>
    </div>
  );
}
