import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router';
import { useAuth } from '../../features/auth/auth-context.tsx';
import { useProfile } from '../../hooks/use-profile.ts';
import {
  getProfileAvatarUrl,
  getUserInitials,
} from '../../features/profile/profile-view.ts';

const menuItemClassName =
  'block w-full rounded-lg px-3 py-2 text-left text-sm text-zinc-300 hover:bg-zinc-800 hover:text-white';

export function Header() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { profile } = useProfile();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement | null>(null);

  // Close menu on outside click
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

  const avatarUrl = getProfileAvatarUrl(profile);
  const initials = getUserInitials(user?.username, profile?.display_name);

  const handleLogout = () => {
    setMenuOpen(false);
    void logout().then(() => navigate('/login'));
  };

  return (
    <header className="sticky top-0 z-10 border-b border-zinc-800 bg-zinc-950/90 backdrop-blur">
      <div className="mx-auto flex w-full max-w-5xl items-center justify-between px-4 py-3">
        <div className="text-left">
          <p className="text-sm font-medium text-zinc-200">ИнКоллаб</p>
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

          {menuOpen && (
            <div className="absolute right-0 mt-2 w-64 rounded-xl border border-zinc-800 bg-zinc-900 p-2 shadow-2xl">
              <div className="border-b border-zinc-800 px-3 py-2">
                <p className="text-sm font-medium text-zinc-100">
                  {profile?.display_name || user?.username || 'Пользователь'}
                </p>
                <p className="truncate text-xs text-zinc-500">{user?.email}</p>
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
                  onClick={handleLogout}
                  className={menuItemClassName}
                >
                  Выйти
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
