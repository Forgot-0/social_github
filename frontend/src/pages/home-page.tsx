import { Link } from 'react-router';
import { useAuth } from '../features/auth/auth-context.tsx';

export function HomePage() {
  const { user } = useAuth();

  return (
    <section className="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-8">
      <h1 className="text-2xl font-semibold">
        Добро пожаловать{user ? `, ${user.username}` : ''}
      </h1>
      <p className="mt-2 text-zinc-400">
        Вы успешно вошли в систему. Перейдите в профиль, чтобы открыть личный
        кабинет и управлять аккаунтом.
      </p>

      <div className="mt-6 flex flex-wrap gap-3">
        <Link
          to="/profile"
          className="rounded-lg bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-900 hover:bg-white"
        >
          Открыть профиль
        </Link>
        <Link
          to="/profile"
          className="rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-300 hover:bg-zinc-800 hover:text-white"
        >
          Личный кабинет
        </Link>
      </div>
    </section>
  );
}
