import { Link } from 'react-router';
import { Button } from './ui/button';
import { ArrowRight, Sparkles } from 'lucide-react';

export function HeroBanner() {
  return (
    <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white rounded-2xl p-8 md:p-12 mb-8">
      <div className="max-w-3xl">
        <div className="inline-flex items-center gap-2 bg-white/20 backdrop-blur-sm rounded-full px-4 py-2 mb-4">
          <Sparkles className="w-4 h-4" />
          <span className="text-sm font-medium">Новая платформа для проектов</span>
        </div>
        
        <h1 className="text-4xl md:text-5xl font-bold mb-4">
          Найди команду своей мечты
        </h1>
        
        <p className="text-lg md:text-xl text-blue-100 mb-8 max-w-2xl">
          InCollab соединяет талантливых специалистов с интересными проектами. 
          Создавай, присоединяйся, реализуй свои идеи вместе!
        </p>
        
        <div className="flex flex-wrap gap-4">
          <Link to="/create-project">
            <Button size="lg" variant="secondary" className="gap-2">
              Создать проект
              <ArrowRight className="w-4 h-4" />
            </Button>
          </Link>
          <Link to="/register">
            <Button size="lg" variant="outline" className="bg-white/10 hover:bg-white/20 border-white/20 text-white">
              Начать поиск
            </Button>
          </Link>
        </div>

        <div className="mt-8 grid grid-cols-3 gap-6 max-w-md">
          <div>
            <div className="text-3xl font-bold">150+</div>
            <div className="text-sm text-blue-100">Участников</div>
          </div>
          <div>
            <div className="text-3xl font-bold">45</div>
            <div className="text-sm text-blue-100">Проектов</div>
          </div>
          <div>
            <div className="text-3xl font-bold">89%</div>
            <div className="text-sm text-blue-100">Успешных матчей</div>
          </div>
        </div>
      </div>
    </div>
  );
}
