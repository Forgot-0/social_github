import { Link, useLocation, useNavigate } from 'react-router';
import { Button } from './ui/button';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuLabel, 
  DropdownMenuSeparator, 
  DropdownMenuTrigger 
} from './ui/dropdown-menu';
import { Home, Briefcase, PlusCircle, User, Settings, LogOut, FolderOpen } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useProfileQuery } from '../../api/hooks/useProfiles';

export function Header() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuth();
  
  const { data: profile } = useProfileQuery(user?.id || 0, {
    enabled: !!user?.id,
  });
  
  const isActive = (path: string) => {
    return location.pathname === path;
  };

  const handleLogout = async () => {
    await logout();
    navigate('/auth/login');
  };

  const avatarUrl = profile?.avatars?.['small'] || profile?.avatars?.['medium'] || profile?.avatars?.['original'];
  const displayName = profile?.display_name || user?.username || 'User';

  return (
    <header className="border-b bg-white sticky top-0 z-50">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <Link to="/" className="text-xl font-bold text-blue-600">
            ProjectHub
          </Link>
          
          <nav className="hidden md:flex items-center gap-1">
            <Link to="/">
              <Button 
                variant={isActive('/') ? 'secondary' : 'ghost'} 
                className="gap-2"
              >
                <Home className="w-4 h-4" />
                Лента
              </Button>
            </Link>
            
            <Link to="/positions">
              <Button 
                variant={isActive('/positions') ? 'secondary' : 'ghost'} 
                className="gap-2"
              >
                <Briefcase className="w-4 h-4" />
                Вакансии
              </Button>
            </Link>
            
            {isAuthenticated && (
              <Link to="/my-projects">
                <Button 
                  variant={isActive('/my-projects') ? 'secondary' : 'ghost'} 
                  className="gap-2"
                >
                  <FolderOpen className="w-4 h-4" />
                  Мои проекты
                </Button>
              </Link>
            )}
          </nav>
        </div>

        <div className="flex items-center gap-3">
          {isAuthenticated ? (
            <>
              <Link to="/create-project">
                <Button className="gap-2">
                  <PlusCircle className="w-4 h-4" />
                  <span className="hidden sm:inline">Создать проект</span>
                </Button>
              </Link>

              <DropdownMenu>
                <DropdownMenuTrigger className="rounded-full focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2">
                  <Avatar className="h-10 w-10 cursor-pointer">
                    <AvatarImage src={avatarUrl} alt={displayName} />
                    <AvatarFallback>{displayName[0]?.toUpperCase() || 'U'}</AvatarFallback>
                  </Avatar>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuLabel>
                    <div className="flex flex-col">
                      <span className="font-medium">{displayName}</span>
                      <span className="text-xs text-muted-foreground">{user?.email || ''}</span>
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => navigate('/profile')}>
                    <User className="mr-2 h-4 w-4" />
                    Профиль
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => navigate('/settings')}>
                    <Settings className="mr-2 h-4 w-4" />
                    Настройки
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem className="text-red-600" onClick={handleLogout}>
                    <LogOut className="mr-2 h-4 w-4" />
                    Выйти
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </>
          ) : (
            <>
              <Link to="/auth/login">
                <Button variant="ghost">Войти</Button>
              </Link>
              <Link to="/auth/register">
                <Button>Регистрация</Button>
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}