import { Link } from 'react-router';

export function Footer() {
  return (
    <footer className="border-t border-zinc-800 bg-zinc-950">
      <div className="mx-auto grid w-full max-w-5xl gap-6 px-4 py-6 text-sm text-zinc-400 md:grid-cols-3">
        <div>
          <p className="text-zinc-100">ИнКоллаб</p>
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
            <Link to="/profile?tab=overview" className="block hover:text-white">
              Личный кабинет
            </Link>
            <Link to="/profile?tab=edit" className="block hover:text-white">
              Редактирование профиля
            </Link>
            <Link to="/profile?tab=security" className="block hover:text-white">
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
  );
}
