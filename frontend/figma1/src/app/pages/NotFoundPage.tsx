import { Link } from 'react-router';
import { Button } from '../components/ui/button';
import { Home } from 'lucide-react';

export function NotFoundPage() {
  return (
    <div className="container mx-auto px-4 py-16">
      <div className="max-w-md mx-auto text-center">
        <h1 className="text-6xl font-bold text-gray-300 mb-4">404</h1>
        <h2 className="text-2xl font-semibold mb-4">Страница не найдена</h2>
        <p className="text-muted-foreground mb-8">
          К сожалению, запрашиваемая страница не существует или была перемещена.
        </p>
        <Link to="/">
          <Button className="gap-2">
            <Home className=""></Home>
            </Button>
        </Link>
        </div>
        </div>
    )
}