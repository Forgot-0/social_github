import { useEffect, useRef, useState } from 'react';
import { Link, Navigate, Outlet, useNavigate } from 'react-router';
import { useAuth } from '../features/auth/auth-context.tsx';
import { listProfiles } from '../services/profiles/profiles.service.ts';
import type { ProfileDTO } from '../types/api/profile.ts';
import {
  getProfileAvatarUrl,
  getUserInitials,
} from '../features/profile/profile-view.ts';

export function AuthenticatedLayout() {
  const navigate = useNavigate();
  const { isReady, isAuthenticated, user, logout } = useAuth();
  const [profile, setProfile] = useState<ProfileDTO | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!user?.username) return;
    let active = true;
    (async () => {
      try {
        const response = await listProfiles({
          username: user.username,
          page_size: 1,
        });
        if (!active) return;
        setProfile(response.items?.[0] ?? null);
      } catch {
        if (active) setProfile(null);
      }
    })();

    return () => {
      active = false;
    };
  }, [user?.username]);

  useEffect(() => {
    const onOutsideClick = (event: MouseEvent) => {
      if (!menuRef.current) return;
      if (!menuRef.current.contains(event.target as Node)) {
        setMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', onOutsideClick);
    return () => {
      document.removeEventListener('mousedown', onOutsideClick);
    };
  }, []);

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

  const avatarUrl = getProfileAvatarUrl(profile);
  const initials = getUserInitials(user?.username, profile?.display_name);
  const menuItemClassName =
    'block w-full rounded-lg px-3 py-2 text-left text-sm text-zinc-300 hover:bg-zinc-800 hover:text-white';

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <header className="sticky top-0 z-10 border-b border-zinc-800 bg-zinc-950/90 backdrop-blur">
        <div className="mx-auto flex w-full max-w-5xl items-center justify-between px-4 py-3">
          <div className="text-left">
            <p className="text-sm font-medium text-zinc-200">Social GitHub</p>
            <p className="text-xs text-zinc-500">Рабочее пространство</p>
          </div>

          <div className="relative" ref={menuRef}>
            <button
              type="button"
              onClick={() => setMenuOpen((prev) => !prev)}
              className="inline-flex h-11 w-11 items-center justify-center overflow-hidden rounded-full border border-zinc-700 bg-zinc-900 hover:border-zinc-500"
              aria-haspopup="menu"
              aria-expanded={menuOpen}
              aria-label="Открыть меню профиля"
            >
              {avatarUrl ? (
                <img
                  src={avatarUrl}
                  alt="Аватар профиля"
                  className="h-full w-full object-cover"
                />
              ) : (
                <span className="text-sm font-semibold text-zinc-200">
                  {initials}
                </span>
              )}
            </button>

            {menuOpen ? (
              <div className="absolute right-0 mt-2 w-64 rounded-xl border border-zinc-800 bg-zinc-900 p-2 shadow-2xl">
                <div className="border-b border-zinc-800 px-3 py-2">
                  <p className="text-sm font-medium text-zinc-100">
                    {profile?.display_name || user?.username || 'Пользователь'}
                  </p>
                  <p className="truncate text-xs text-zinc-500">
                    {user?.email}
                  </p>
                </div>

                <div className="mt-2 space-y-1">
                  <Link
                    to="/"
                    className={menuItemClassName}
                    onClick={() => setMenuOpen(false)}
                  >
                    Главная
                  </Link>
                  <Link
                    to="/profile?tab=overview"
                    className={menuItemClassName}
                    onClick={() => setMenuOpen(false)}
                  >
                    Личный кабинет
                  </Link>
                  <Link
                    to="/profile?tab=edit"
                    className={menuItemClassName}
                    onClick={() => setMenuOpen(false)}
                  >
                    Редактирование профиля
                  </Link>
                  <Link
                    to="/profile?tab=security"
                    className={menuItemClassName}
                    onClick={() => setMenuOpen(false)}
                  >
                    Безопасность и сессии
                  </Link>
                </div>

                <div className="mt-2 border-t border-zinc-800 pt-2">
                  <button
                    type="button"
                    onClick={() => {
                      setMenuOpen(false);
                      void logout().then(() => navigate('/login'));
                    }}
                    className={menuItemClassName}
                  >
                    Выйти
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl px-4 py-8">
        <Outlet />
      </main>

      <footer className="border-t border-zinc-800 bg-zinc-950">
        <div className="mx-auto grid w-full max-w-5xl gap-6 px-4 py-6 text-sm text-zinc-400 md:grid-cols-3">
          <div>
            <p className="text-zinc-100">Social GitHub</p>
            <p className="mt-2 text-xs text-zinc-500">
              Единое пространство для профиля, проектов и командной работы.
            </p>
          </div>

          <div>
            <p className="text-zinc-200">Основные разделы</p>
            <div className="mt-2 space-y-1 text-xs">
              <Link to="/" className="block hover:text-white">
                Главная
              </Link>
              <Link
                to="/profile?tab=overview"
                className="block hover:text-white"
              >
                Личный кабинет
              </Link>
              <Link to="/profile?tab=edit" className="block hover:text-white">
                Редактирование профиля
              </Link>
              <Link
                to="/profile?tab=security"
                className="block hover:text-white"
              >
                Безопасность
              </Link>
            </div>
          </div>

          <div>
            <p className="text-zinc-200">Важное</p>
            <div className="mt-2 space-y-1 text-xs">
              <a href="#" className="block hover:text-white">
                Политика конфиденциальности
              </a>
              <a href="#" className="block hover:text-white">
                Условия использования
              </a>
              <a href="#" className="block hover:text-white">
                Поддержка и обратная связь
              </a>
              <a href="#" className="block hover:text-white">
                Центр безопасности
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
