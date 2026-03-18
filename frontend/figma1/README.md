# 🚀 ProjectHub - Платформа поиска участников проектов

> Современная веб-платформа для студентов и стартапов, помогающая формировать команды и находить интересные проекты.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![React](https://img.shields.io/badge/React-18.3.1-61dafb.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178c6.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 📖 О проекте

**ProjectHub** - это платформа, которая соединяет создателей проектов с талантливыми исполнителями. Идеально подходит для:

- 🎓 **Студентов**, ищущих участников для учебных проектов
- 💡 **Стартаперов**, формирующих команды
- 🏢 **Компаний**, ищущих специалистов под конкретные задачи
- 👨‍💻 **Разработчиков**, желающих найти интересные проекты

## ✨ Основные возможности

### Для создателей проектов
- ✅ Создание и управление проектами
- ✅ Публикация вакансий с требованиями
- ✅ Получение откликов от кандидатов
- ✅ Система рекомендаций подходящих специалистов
- ✅ Управление командой и ролями

### Для соискателей
- ✅ Персонализированная лента проектов
- ✅ Умная фильтрация по навыкам
- ✅ Простые отклики на позиции
- ✅ Отслеживание статуса заявок
- ✅ Профиль с портфолио навыков

### Дополнительно
- 🔐 Безопасная аутентификация (JWT + OAuth)
- 📊 Статистика и аналитика
- 🎨 Современный адаптивный дизайн
- 🌍 Полная локализация (русский)
- 💼 Гибкая система подписок

## 🛠 Технологии

### Frontend
- **React 18.3.1** - UI библиотека
- **TypeScript** - типизация
- **React Router v7** - маршрутизация (Data Mode)
- **Tailwind CSS v4** - стили
- **Radix UI** - доступные компоненты
- **shadcn/ui** - UI kit
- **Motion** (Framer Motion) - анимации
- **React Hook Form** - формы
- **Sonner** - уведомления
- **date-fns** - работа с датами

### Backend (API Ready)
- **FastAPI** - REST API
- **PostgreSQL** - база данных
- **JWT** - аутентификация
- **OAuth 2.0** - социальная авторизация

## 🚀 Быстрый старт

### Установка

```bash
# Клонируйте репозиторий
git clone https://github.com/your-username/projecthub.git

# Перейдите в директорию
cd projecthub

# Установите зависимости
npm install

# Запустите dev сервер
npm run dev
```

Приложение будет доступно на `http://localhost:5173`

### Демо-доступ

Для входа в демо-версию используйте:
- **Username**: `demo`
- **Password**: `demo`

## 📁 Структура проекта

```
projecthub/
├── src/
│   ├── app/
│   │   ├── components/     # React компоненты
│   │   │   ├── ui/        # shadcn/ui компоненты
│   │   │   ├── Header.tsx
│   │   │   ├── Footer.tsx
│   │   │   ├── ProjectCard.tsx
│   │   │   └── ...
│   │   ├── pages/         # Страницы приложения
│   │   │   ├── HomePage.tsx
│   │   │   ├── LoginPage.tsx
│   │   │   ├── ProjectDetailPage.tsx
│   │   │   └── ...
│   │   ├── services/      # API клиент
│   │   │   └── api.ts
│   │   ├── data/          # Моковые данные
│   │   │   └── mockData.ts
│   │   ├── layouts/       # Layouts
│   │   │   └── RootLayout.tsx
│   │   ├── types.ts       # TypeScript типы
│   │   ├── routes.tsx     # Роутинг
│   │   └── App.tsx        # Главный компонент
│   └── styles/            # Стили
├── API_INTEGRATION.md     # Руководство по API
├── GETTING_STARTED.md     # Руководство пользователя
├── README_PROJECT.md      # Проектная документация
└── package.json
```

## 🎨 Скриншоты

### Главная страница
Лента проектов с фильтрацией и поиском, статистика платформы

### Детали проекта
Подробная информация о проекте, вакансии, команда

### Мои проекты
Управление созданными проектами и откликами

### Профиль
Персональная страница с навыками и проектами

## 🔌 API Интеграция

Приложение готово к интеграции с FastAPI backend. См. [API_INTEGRATION.md](./API_INTEGRATION.md)

### Текущий статус

- ✅ Auth endpoints (login, register, OAuth)
- ✅ Users endpoints (профиль, список)
- ⏳ Projects endpoints (в разработке)
- ⏳ Positions endpoints (в разработке)
- ⏳ Applications endpoints (в разработке)
- ⏳ Skills endpoints (в разработке)

### Настройка API

```bash
# Создайте .env файл
echo "VITE_API_BASE_URL=http://localhost:8000" > .env

# Запустите backend (отдельный репозиторий)
# Приложение автоматически подключится к API
```

## 📚 Документация

- [Руководство пользователя](./GETTING_STARTED.md) - Как начать работу
- [API Integration](./API_INTEGRATION.md) - Интеграция с backend
- [Проектная документация](./README_PROJECT.md) - Детальное описание

## 🎯 Roadmap

### Phase 1 (Текущая)
- [x] UI/UX дизайн
- [x] Аутентификация
- [x] Управление проектами
- [x] Система откликов
- [x] Профили пользователей

### Phase 2 (В разработке)
- [ ] Интеграция с backend API
- [ ] Система уведомлений
- [ ] Чат между участниками
- [ ] Аналитика проектов
- [ ] Расширенный поиск

### Phase 3 (Планируется)
- [ ] Mobile приложение
- [ ] Интеграция с GitHub
- [ ] Система рейтингов
- [ ] AI рекомендации
- [ ] Export/Import проектов

## 🤝 Вклад в проект

Мы приветствуем вклад в развитие проекта!

1. Fork репозиторий
2. Создайте feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit изменения (`git commit -m 'Add some AmazingFeature'`)
4. Push в branch (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. [LICENSE](./LICENSE) для деталей.

## 👥 Команда

- **Frontend Developer** - React, TypeScript, Tailwind
- **Backend Developer** - FastAPI, PostgreSQL
- **UI/UX Designer** - Figma, Design System

## 📞 Контакты

- **Email**: support@projecthub.com
- **Website**: https://projecthub.com
- **GitHub**: https://github.com/projecthub

## 🙏 Благодарности

- [shadcn/ui](https://ui.shadcn.com/) - за отличные UI компоненты
- [Radix UI](https://www.radix-ui.com/) - за accessibility
- [Lucide](https://lucide.dev/) - за иконки
- [Unsplash](https://unsplash.com/) - за изображения

---

**Сделано с ❤️ для студентов и стартаперов**
