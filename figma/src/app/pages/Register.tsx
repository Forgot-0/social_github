import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, User } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'sonner';
import { AppLogo } from '../components/AppLogo';

export function Register() {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    repeat_password: '',
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (formData.password !== formData.repeat_password) {
      toast.error('Пароли не совпадают');
      return;
    }

    setLoading(true);
    try {
      await register(formData);
      navigate('/login');
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
          <h1 className="mb-6 text-center text-2xl font-bold">Регистрация</h1>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="mb-2 block text-sm">Имя пользователя</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="text"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  placeholder="username"
                  required
                  minLength={4}
                  maxLength={100}
                  className="app-input w-full pl-10 pr-4"
                />
              </div>
              <p className="mt-1 text-xs text-muted-foreground">4-100 символов</p>
            </div>

            <div>
              <label className="mb-2 block text-sm">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="email@example.com"
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
                  minLength={8}
                  maxLength={128}
                  className="app-input w-full pl-10 pr-4"
                />
              </div>
              <p className="mt-1 text-xs text-muted-foreground">8-128 символов</p>
            </div>

            <div>
              <label className="mb-2 block text-sm">Подтверждение пароля</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="password"
                  value={formData.repeat_password}
                  onChange={(e) => setFormData({ ...formData, repeat_password: e.target.value })}
                  placeholder="Повторите пароль"
                  required
                  className="app-input w-full pl-10 pr-4"
                />
              </div>
            </div>

            <div className="flex items-start space-x-2">
              <input type="checkbox" required className="mt-1 rounded border-border" />
              <label className="text-sm text-muted-foreground">
                Я согласен с{' '}
                <a href="#" className="text-primary hover:underline">
                  условиями использования
                </a>{' '}
                и{' '}
                <a href="#" className="text-primary hover:underline">
                  политикой конфиденциальности
                </a>
              </label>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-primary py-3 font-semibold text-white transition-colors hover:bg-accent disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? 'Регистрация...' : 'Создать аккаунт'}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-muted-foreground">
            Уже есть аккаунт?{' '}
            <Link to="/login" className="font-semibold text-primary hover:underline">
              Войти
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
