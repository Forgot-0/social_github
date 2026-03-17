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
import { Home, Briefcase, PlusCircle, User, Settings, LogOut } from 'lucide-react';
import { CURRENT_USER } from '../data/mockData';
import { clearAccessToken } from '../services/api';
import { toast } from 'sonner';

export function Header() {
  const location = useLocation();
  const navigate = useNavigate();
  
  const isActive = (path: string) => {
    return location.pathname === path;
  };

  const handleLogout = () => {
    clearAccessToken();
    toast.success('Вы вышли из системы');
    navigate('/login');
  };

  return (
    <header className="border-b bg-white sticky top-0 z-50">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <Link to="/" className="text-xl font-bold text-blue-600">
            InCollab
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
            <Link to="/my-projects">
              <Button 
                variant={isActive('/my-projects') ? 'secondary' : 'ghost'} 
                className="gap-2"
              >
                <Briefcase className="w-4 h-4" />
                Мои проекты
              </Button>
            </Link>
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <Link to="/create-project">
            <Button className="gap-2">
              <PlusCircle className="w-4 h-4" />
              <span className="hidden sm:inline">Создать проект</span>
            </Button>
          </Link>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="relative h-10 w-10 rounded-full">
                <Avatar>
                  <AvatarImage src={CURRENT_USER.avatar} alt={CURRENT_USER.name} />
                  <AvatarFallback>{CURRENT_USER.name[0]}</AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel>
                <div className="flex flex-col">
                  <span className="font-medium">{CURRENT_USER.name}</span>
                  <span className="text-xs text-muted-foreground">{CURRENT_USER.email}</span>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <Link to="/profile">
                <DropdownMenuItem>
                  <User className="mr-2 h-4 w-4" />
                  Профиль
                </DropdownMenuItem>
              </Link>
              <Link to="/settings">
                <DropdownMenuItem>
                  <Settings className="mr-2 h-4 w-4" />
                  Настройки
                </DropdownMenuItem>
              </Link>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="text-red-600" onClick={handleLogout}>
                <LogOut className="mr-2 h-4 w-4" />
                Выйти
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
}