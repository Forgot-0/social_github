import { Link } from 'react-router';
import { Button } from './ui/button';
import { ArrowRight, Sparkles, Users, Briefcase, TrendingUp } from 'lucide-react';

export function HeroBanner() {
  return (
    <div className="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-700 text-white rounded-3xl p-8 md:p-12 mb-8 shadow-xl">
      <div className="max-w-4xl">
        <div className="inline-flex items-center gap-2 bg-white/20 backdrop-blur-sm rounded-full px-4 py-2 mb-6">
          <Sparkles className="w-4 h-4" />
          <span className="text-sm font-medium">Платформа для команд и проектов</span>
        </div>
        
        <h1 className="text-4xl md:text-6xl font-bold mb-6 leading-tight">
          Найди команду <br />своей мечты
        </h1>
        
        <p className="text-lg md:text-xl text-blue-100 mb-8 max-w-2xl leading-relaxed">
          ProjectHub соединяет талантливых специалистов с интересными проектами. 
          Создавай, присоединяйся, реализуй свои идеи вместе!
        </p>
        
        <div className="flex flex-wrap gap-4 mb-12">
          <Link to="/auth/register">
            <Button size="lg" variant="secondary" className="gap-2 shadow-lg">
              Начать поиск
              <ArrowRight className="w-4 h-4" />
            </Button>
          </Link>
          <Link to="/positions">
            <Button size="lg" variant="outline" className="bg-white/10 hover:bg-white/20 border-white/30 text-white backdrop-blur-sm">
              Смотреть вакансии
            </Button>
          </Link>
        </div>

        <div className="grid grid-cols-3 gap-8 max-w-2xl">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 bg-white/20 backdrop-blur-sm rounded-xl mb-3">
              <Users className="w-6 h-6" />
            </div>
            <div className="text-3xl font-bold mb-1">500+</div>
            <div className="text-sm text-blue-100">Участников</div>
          </div>
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 bg-white/20 backdrop-blur-sm rounded-xl mb-3">
              <Briefcase className="w-6 h-6" />
            </div>
            <div className="text-3xl font-bold mb-1">120+</div>
            <div className="text-sm text-blue-100">Проектов</div>
          </div>
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 bg-white/20 backdrop-blur-sm rounded-xl mb-3">
              <TrendingUp className="w-6 h-6" />
            </div>
            <div className="text-3xl font-bold mb-1">92%</div>
            <div className="text-sm text-blue-100">Успешных матчей</div>
          </div>
        </div>
      </div>
    </div>
  );
}