import { useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router';
import { useAuth } from '../../features/auth/auth-context.tsx';
import { isApiError } from '../../features/auth/api-error.ts';

export function RegisterPage() {
  const navigate = useNavigate();
  const { isReady, isAuthenticated, register, login } = useAuth();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [repeatPassword, setRepeatPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  if (isReady && isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (password !== repeatPassword) {
      setError('Пароли не совпадают');
      return;
    }
    setPending(true);
    try {
      await register({
        username: username.trim(),
        email: email.trim(),
        password,
        repeat_password: repeatPassword,
      });
      try {
        await login(username.trim(), password);
        navigate('/', { replace: true });
      } catch {
        navigate('/login', { replace: true });
      }
    } catch (err) {
      setError(isApiError(err) ? err.message : 'Не удалось зарегистрироваться');
    } finally {
      setPending(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-950 px-4 py-12">
      <div className="w-full max-w-md space-y-8 rounded-2xl border border-zinc-800 bg-zinc-900/80 p-8 shadow-xl backdrop-blur">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-50">
            Регистрация
          </h1>
          <p className="mt-2 text-sm text-zinc-400">
            Пароль: 8–128 символов, заглавная и строчная буква, цифра и
            спецсимвол из набора API (например{' '}
            <span className="font-mono text-zinc-300">{`!@#$%^&*(),.?":{}|<>`}</span>
            ).
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
              htmlFor="reg-username"
              className="block text-sm font-medium text-zinc-300"
            >
              Имя пользователя
            </label>
            <input
              id="reg-username"
              name="username"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              minLength={4}
              className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100 outline-none focus:border-zinc-500 focus:ring-2 focus:ring-zinc-500"
            />
          </div>
          <div>
            <label
              htmlFor="reg-email"
              className="block text-sm font-medium text-zinc-300"
            >
              Email
            </label>
            <input
              id="reg-email"
              name="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100 outline-none focus:border-zinc-500 focus:ring-2 focus:ring-zinc-500"
            />
          </div>
          <div>
            <label
              htmlFor="reg-password"
              className="block text-sm font-medium text-zinc-300"
            >
              Пароль
            </label>
            <input
              id="reg-password"
              name="password"
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100 outline-none focus:border-zinc-500 focus:ring-2 focus:ring-zinc-500"
            />
          </div>
          <div>
            <label
              htmlFor="reg-repeat"
              className="block text-sm font-medium text-zinc-300"
            >
              Повтор пароля
            </label>
            <input
              id="reg-repeat"
              name="repeat_password"
              type="password"
              autoComplete="new-password"
              value={repeatPassword}
              onChange={(e) => setRepeatPassword(e.target.value)}
              required
              className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100 outline-none focus:border-zinc-500 focus:ring-2 focus:ring-zinc-500"
            />
          </div>
          <button
            type="submit"
            disabled={pending || !isReady}
            className="w-full rounded-lg bg-zinc-100 py-2.5 text-sm font-medium text-zinc-900 transition hover:bg-white disabled:opacity-50"
          >
            {pending ? 'Регистрация…' : 'Создать аккаунт'}
          </button>
        </form>

        <p className="text-center text-sm text-zinc-500">
          Уже есть аккаунт?{' '}
          <Link
            to="/login"
            className="font-medium text-zinc-300 underline-offset-4 hover:text-white hover:underline"
          >
            Вход
          </Link>
        </p>
      </div>
    </div>
  );
}
