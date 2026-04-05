import { useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router';
import { useAuth } from '../../features/auth/auth-context.tsx';
import { isApiError } from '../../features/auth/api-error.ts';
import {
  OAUTH_PROVIDERS,
  type OAuthProvider,
} from '../../features/auth/oauth-providers.ts';

const providerLabels: Record<OAuthProvider, string> = {
  google: 'Google',
  yandex: 'Яндекс',
  github: 'GitHub',
};

export function LoginPage() {
  const navigate = useNavigate();
  const { isReady, isAuthenticated, login, startOAuthLogin } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  if (isReady && isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setPending(true);
    try {
      await login(username.trim(), password);
      navigate('/', { replace: true });
    } catch (err) {
      setError(isApiError(err) ? err.message : 'Не удалось войти');
    } finally {
      setPending(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-950 px-4 py-12">
      <div className="w-full max-w-md space-y-8 rounded-2xl border border-zinc-800 bg-zinc-900/80 p-8 shadow-xl backdrop-blur">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-50">
            Вход
          </h1>
          <p className="mt-2 text-sm text-zinc-400">
            Access token хранится в памяти; сессия обновляется через cookie{' '}
            <code className="rounded bg-zinc-800 px-1 py-0.5 text-xs text-zinc-300">
              refresh_token
            </code>
            .
          </p>
        </div>

        {error ? (
          <div
            className="rounded-lg border border-red-900/60 bg-red-950/40 px-3 py-2 text-sm text-red-200"
            role="alert"
          >
            {error}
          </div>
        ) : null}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="login-username"
              className="block text-sm font-medium text-zinc-300"
            >
              Имя пользователя
            </label>
            <input
              id="login-username"
              name="username"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100 outline-none focus:border-zinc-500 focus:ring-2 focus:ring-zinc-500"
            />
          </div>
          <div>
            <label
              htmlFor="login-password"
              className="block text-sm font-medium text-zinc-300"
            >
              Пароль
            </label>
            <input
              id="login-password"
              name="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100 outline-none focus:border-zinc-500 focus:ring-2 focus:ring-zinc-500"
            />
          </div>
          <button
            type="submit"
            disabled={pending || !isReady}
            className="w-full rounded-lg bg-zinc-100 py-2.5 text-sm font-medium text-zinc-900 transition hover:bg-white disabled:opacity-50"
          >
            {pending ? 'Вход…' : 'Войти'}
          </button>
        </form>

        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-zinc-800" />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-zinc-900/80 px-2 text-zinc-500">
              или через OAuth
            </span>
          </div>
        </div>

        <div className="grid gap-2 sm:grid-cols-3">
          {OAUTH_PROVIDERS.map((p) => (
            <button
              key={p}
              type="button"
              disabled={!isReady}
              onClick={() => startOAuthLogin(p)}
              className="rounded-lg border border-zinc-700 bg-zinc-950 py-2 text-sm font-medium text-zinc-200 transition hover:border-zinc-500 hover:bg-zinc-800 disabled:opacity-50"
            >
              {providerLabels[p]}
            </button>
          ))}
        </div>

        <p className="text-center text-sm text-zinc-500">
          Нет аккаунта?{' '}
          <Link
            to="/register"
            className="font-medium text-zinc-300 underline-offset-4 hover:text-white hover:underline"
          >
            Регистрация
          </Link>
        </p>
      </div>
    </div>
  );
}
