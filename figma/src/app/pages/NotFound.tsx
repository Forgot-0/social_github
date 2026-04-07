import { Link } from "react-router-dom";
import { Home as HomeIcon, Search } from "lucide-react";

export function NotFound() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center px-4">
      <div className="text-center">
        <div className="text-9xl font-bold text-primary/20 mb-4">404</div>
        <h1 className="text-3xl md:text-4xl font-bold mb-4">Страница не найдена</h1>
        <p className="text-lg text-muted-foreground mb-8 max-w-md mx-auto">
          К сожалению, страница, которую вы ищете, не существует или была перемещена
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            to="/"
            className="inline-flex items-center justify-center space-x-2 px-6 py-3 bg-primary text-white rounded-lg hover:bg-accent transition-colors"
          >
            <HomeIcon className="w-5 h-5" />
            <span>На главную</span>
          </Link>
          <Link
            to="/projects"
            className="inline-flex items-center justify-center space-x-2 px-6 py-3 border-2 border-primary text-primary rounded-lg hover:bg-secondary transition-colors"
          >
            <Search className="w-5 h-5" />
            <span>Поиск проектов</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
