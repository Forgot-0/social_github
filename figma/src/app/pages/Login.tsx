import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Mail, Lock } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { AppLogo } from '../components/AppLogo';

export function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);

  const from = (location.state as any)?.from?.pathname || '/';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(formData.username, formData.password);
      navigate(from, { replace: true });
    } catch {
      // Error is handled in AuthContext with toast
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <AppLogo size="lg" className="justify-center" />
        </div>

        <div className="rounded-xl border border-border bg-white p-8 shadow-lg">
          <h1 className="mb-6 text-center text-2xl font-bold">Вход в аккаунт</h1>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="mb-2 block text-sm">Имя пользователя или Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="text"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  placeholder="username или email@example.com"
                  required
                  className="app-input w-full pl-10 pr-4"
                />
              </div>
            </div>

            <div>
              <label className="mb-2 block text-sm">Пароль</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  placeholder="Введите пароль"
                  required
                  className="app-input w-full pl-10 pr-4"
                />
              </div>
            </div>

            <div className="flex items-center justify-between text-sm">
              <label className="flex cursor-pointer items-center space-x-2">
                <input type="checkbox" className="rounded border-border" />
                <span className="text-muted-foreground">Запомнить меня</span>
              </label>
              <a href="#" className="text-primary hover:underline">
                Забыли пароль?
              </a>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-primary py-3 font-semibold text-white transition-colors hover:bg-accent disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? 'Вход...' : 'Войти'}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-muted-foreground">
            Нет аккаунта?{' '}
            <Link to="/register" className="font-semibold text-primary hover:underline">
              Зарегистрироваться
            </Link>
          </div>
        </div>

        <div className="mt-6 text-center">
          <Link to="/" className="text-sm text-muted-foreground hover:text-primary">
            ← Вернуться на главную
          </Link>
        </div>
      </div>
    </div>
  );
}
