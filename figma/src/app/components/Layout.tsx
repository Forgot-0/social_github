import { Outlet, Link, useLocation } from 'react-router-dom';
import { Home, Briefcase, FolderOpen, LogIn, Menu, X, MessageCircle, ClipboardList, Users } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { AppLogo } from './AppLogo';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { api } from '../lib/api';

interface ProfileAvatarData {
  avatars?: Record<string, { url?: string } | string>;
  display_name?: string;
}

async function loadProfileForUser(userId: number): Promise<ProfileAvatarData | null> {
  try {
    return await api.getProfile(userId);
  } catch {
    return null;
  }
}

function getInitials(value?: string) {
  if (!value) return 'И';
  return value.trim()[0]?.toUpperCase() || 'И';
}

export function Layout() {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [avatarUrl, setAvatarUrl] = useState<string>('');
  const [displayName, setDisplayName] = useState<string>('');
  const { user } = useAuth();

  const navigation = useMemo(() => {
    const publicItems = [
      { name: 'Главная', href: '/', icon: Home },
      { name: 'Проекты', href: '/projects', icon: FolderOpen },
      { name: 'Позиции', href: '/positions', icon: Briefcase },
      { name: 'Люди', href: '/people', icon: Users },
    ];

    if (!user) {
      return publicItems;
    }

    return [
      ...publicItems,
      { name: 'Мои проекты', href: '/my-projects', icon: FolderOpen },
      { name: 'Отклики', href: '/applications', icon: ClipboardList },
      { name: 'Чаты', href: '/chat', icon: MessageCircle },
    ];
  }, [user]);

  useEffect(() => {
    let cancelled = false;

    const syncProfileBadge = async () => {
      if (!user) {
        setAvatarUrl('');
        setDisplayName('');
        return;
      }

      const profile = await loadProfileForUser(user.id);
      if (cancelled) return;
      const avatars = profile?.avatars || {};
      const preferredAvatar = avatars['128'] || avatars['256'] || avatars.small || avatars.medium || avatars.large;
      const avatarValue = typeof preferredAvatar === 'string'
        ? preferredAvatar
        : preferredAvatar && typeof preferredAvatar === 'object' && 'url' in preferredAvatar
          ? String((preferredAvatar as any).url)
          : '';
      setAvatarUrl(avatarValue);
      setDisplayName(profile?.display_name || user.username);
    };

    void syncProfileBadge();

    const handleProfileUpdated = () => {
      void syncProfileBadge();
    };

    window.addEventListener('profile-updated', handleProfileUpdated);
    return () => {
      cancelled = true;
      window.removeEventListener('profile-updated', handleProfileUpdated);
    };
  }, [user]);

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50">
      <header className="sticky top-0 z-50 border-b border-border bg-white/85 backdrop-blur-md">
        <div className="mx-auto flex h-18 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
          <div className="flex min-w-0 items-center gap-4 lg:gap-8">
            <AppLogo size="md" className="min-w-0" />

            <nav className="hidden lg:flex items-center gap-2 xl:gap-3">
              {navigation.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium transition-all ${
                      active
                        ? 'bg-primary text-white shadow-sm'
                        : 'text-muted-foreground hover:bg-secondary hover:text-secondary-foreground'
                    }`}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    <span className="whitespace-nowrap">{item.name}</span>
                  </Link>
                );
              })}
            </nav>
          </div>

          <div className="hidden lg:flex items-center gap-3 shrink-0">
            {user ? (
              <>
                <Link
                  to="/profile"
                  className="group inline-flex items-center justify-center rounded-2xl border border-border bg-white p-1.5 shadow-sm transition-all hover:border-primary/30 hover:bg-secondary/40"
                  aria-label="Открыть профиль"
                  title={displayName || user.username}
                >
                  <Avatar className="h-10 w-10 ring-2 ring-primary/10">
                    <AvatarImage src={avatarUrl} alt={displayName || user.username} className="object-cover" />
                    <AvatarFallback className="bg-primary text-white text-sm font-semibold">
                      {getInitials(displayName || user.username)}
                    </AvatarFallback>
                  </Avatar>
                </Link>
              </>
            ) : (
              <>
                <Link to="/login" className="rounded-xl px-4 py-2.5 text-sm font-medium text-primary transition-colors hover:bg-secondary">
                  Войти
                </Link>
                <Link
                  to="/register"
                  className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-accent"
                >
                  <LogIn className="h-4 w-4" />
                  <span>Регистрация</span>
                </Link>
              </>
            )}
          </div>

          <button
            className="lg:hidden rounded-xl p-2 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
            onClick={() => setMobileMenuOpen((prev) => !prev)}
            aria-label={mobileMenuOpen ? 'Закрыть меню' : 'Открыть меню'}
          >
            {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>

        {mobileMenuOpen && (
          <div className="border-t border-border bg-white lg:hidden">
            <div className="mx-auto max-w-7xl space-y-2 px-4 py-4 sm:px-6 lg:px-8">
              {user && (
                <Link
                  to="/profile"
                  onClick={() => setMobileMenuOpen(false)}
                  className="mb-2 flex items-center gap-3 rounded-2xl bg-secondary/50 p-3"
                >
                  <Avatar className="h-11 w-11">
                    <AvatarImage src={avatarUrl} alt={displayName || user.username} className="object-cover" />
                    <AvatarFallback className="bg-primary text-white font-semibold">
                      {getInitials(displayName || user.username)}
                    </AvatarFallback>
                  </Avatar>
                  <div className="min-w-0">
                    <div className="truncate font-semibold text-foreground">{displayName || user.username}</div>
                    <div className="truncate text-sm text-muted-foreground">@{user.username}</div>
                  </div>
                </Link>
              )}

              {navigation.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center gap-3 rounded-xl px-4 py-3 transition-colors ${
                      active
                        ? 'bg-primary text-white'
                        : 'text-muted-foreground hover:bg-secondary hover:text-secondary-foreground'
                    }`}
                  >
                    <Icon className="h-5 w-5 shrink-0" />
                    <span>{item.name}</span>
                  </Link>
                );
              })}

              <div className="space-y-2 border-t border-border pt-3">
                {user ? null : (
                  <>
                    <Link
                      to="/login"
                      onClick={() => setMobileMenuOpen(false)}
                      className="flex items-center justify-center rounded-xl border border-primary px-4 py-3 text-primary transition-colors hover:bg-secondary"
                    >
                      Войти
                    </Link>
                    <Link
                      to="/register"
                      onClick={() => setMobileMenuOpen(false)}
                      className="flex items-center justify-center gap-2 rounded-xl bg-primary px-4 py-3 text-white transition-colors hover:bg-accent"
                    >
                      <LogIn className="h-5 w-5" />
                      <span>Регистрация</span>
                    </Link>
                  </>
                )}
              </div>
            </div>
          </div>
        )}
      </header>

      <main>
        <Outlet />
      </main>
    </div>
  );
}
