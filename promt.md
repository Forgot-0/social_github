Ты опытный fullstack-разработчик. Перед тобой React/TypeScript-приложение ProjectHub.
Исправь все перечисленные ниже проблемы и реализуй новый функционал.
После исправлений код должен работать корректно с FastAPI backend согласно api-docs.md.

───────────────────────────────────────────
БЛОК 1 — API / ЛОГИКА
───────────────────────────────────────────

1. [КРИТИЧНО] React Query v5: замени все вхождения `.isLoading` на `.isPending`
   в мутациях (не в запросах useQuery — там оставь isLoading).
   Файлы: CreateProjectPage.tsx, SettingsPage.tsx, ProfilePage.tsx и все хуки.

2. [КРИТИЧНО] В CreateProjectPage.tsx поле `description` передаётся в API как:
   `description: description.trim()`
   Проверь api-docs.md: если бэкенд ожидает `full_description` — переименуй.
   Синхронизируй с типом ProjectDTO в api.ts (`full_description` vs `description`).

3. [КРИТИЧНО] Несоответствие типа avatars:
   — В api.ts тип ProfileDTO: `avatars?: Record<string, string>`
   — В ProfilePage.tsx обращение: `profile?.avatars?.['medium']?.['url']`
     (подразумевает Record<string, {url: string}>)
   — В SettingsPage.tsx обращение: `profile?.avatars?.medium`
     (подразумевает Record<string, string>)
   Изучи api-docs.md, определи реальную форму ответа и исправь тип ProfileDTO
   и все места его использования.

4. [КРИТИЧНО] В ProjectDetailPage.tsx кнопка "Просмотреть отклики" в блоке
   управления владельца вызывает `handleViewApplications` без аргумента,
   но функция ожидает `position: PositionDTO`. Исправь — передай null или
   измени логику так, чтобы открывался список всех откликов по проекту,
   а не по конкретной позиции.

5. [ВАЖНО] В MyProjectsPage.tsx лишние параллельные запросы:
   — usePositionsQuery() и useProjectsQuery() грузят ВСЕ позиции и проекты
     только чтобы сопоставить заявки. Это N+1 pattern.
   Исправь: при получении myApplications сразу доставай нужные данные через
   include/expand в запросе (если api-docs.md это поддерживает) или
   делай отдельные запросы только для тех project_id и position_id, которые
   нужны, а не всё подряд.

ВАЖНО: поле `password_repeat` в RegisterPage.tsx и api.ts НЕ трогать —
оставить как есть.

───────────────────────────────────────────
БЛОК 2 — ТИПЫ / TypeScript
───────────────────────────────────────────

6. В api.ts метод `projectsApi.getProjectPositions` возвращает `PositionDTO[]`
   (массив напрямую). Проверь api-docs.md — если эндпоинт
   `GET /api/v1/projects/{id}/positions` возвращает PageResult<PositionDTO>,
   исправь тип и все хуки, которые его используют.

7. В ProjectDetailPage.tsx и других местах обращение к `project.full_description`
   и `project.description` вперемешку. Приведи к единому полю согласно
   api-docs.md и обнови тип ProjectDTO.

8. Проверь тип ApplicationDTO: поле `project_id` присутствует в MyProjectsPage,
   но в api.ts оно не гарантировано в ответе API. Добавь в тип если нужно,
   либо получай project_id через position, а не напрямую.

───────────────────────────────────────────
БЛОК 3 — ДИЗАЙН / UX
───────────────────────────────────────────

9. HeroBanner в HomePage.tsx:
   Показывай баннер только неаутентифицированным пользователям.
   Для аутентифицированных замени на компактный приветственный блок
   с именем пользователя: "Привет, {username}! Найдите новый проект."

10. Статистика в HomePage.tsx захардкожена ("150+", "45", "89%").
    — "Активных проектов" и "Открытых вакансий" вычисляй из реальных данных
      (уже есть projectsData?.total и totalPositions).
    — "Участников" и "Успешных матчей" оберни в placeholder или скрой,
      пока нет реального API для этих метрик.

11. Badge visibility в ProjectCard.tsx:
    `<Badge variant="default">{project.visibility}</Badge>` показывает "public"
    по-английски. Замени на русское: "Публичный" / "Приватный".

12. Вкладки в HomePage.tsx ("Рекомендации", "Новые") показывают те же данные,
    что и "Все проекты" (просто .slice() и .reverse()).
    — "Новые": сортируй по created_at DESC (добавь sort="-created_at" в запрос)
    — "Рекомендации": если API не поддерживает — покажи заглушку с объяснением
      "Заполните профиль и навыки для персональных рекомендаций" вместо дублей.

13. В ProjectDetailPage.tsx нет skeleton-экрана для вкладки "Вакансии" при загрузке
    (positionsLoading). Добавь 2–3 ProjectCardSkeleton или аналогичный
    placeholder пока positionsLoading === true.

───────────────────────────────────────────
БЛОК 4 — НОВЫЙ ФУНКЦИОНАЛ: вкладка «Вакансии» в навбаре
───────────────────────────────────────────

14. Добавь в Header.tsx новую кнопку навигации «Вакансии» между «Лентой» и
    «Моими проектами». Иконка — `Briefcase` из lucide-react (или другая
    подходящая, не занятая). Маршрут: `/positions`.

    Пример структуры кнопки (по аналогии с существующими):
```tsx
    <Link to="/positions">
      <Button variant={isActive('/positions') ? 'secondary' : 'ghost'} className="gap-2">
        <Briefcase className="w-4 h-4" />
        Вакансии
      </Button>
    </Link>
```

    Показывай кнопку всегда (и для авторизованных, и для гостей).

15. Создай новую страницу `src/app/pages/PositionsPage.tsx`:
    — Заголовок страницы: "Все вакансии"
    — Поиск по названию позиции (поле title)
    — Фильтры: тип занятости (location_type: remote/onsite/hybrid),
      нагрузка (expected_load: low/medium/high), только открытые (is_open)
    — Список карточек позиций через существующий компонент PositionCard
    — Каждая карточка ссылается на проект через `project_id`: кнопка
      "Перейти к проекту" → `/projects/{position.project_id}`
    — Пагинация: кнопки «Назад» / «Вперёд», показывай текущую страницу
    — Загрузка: используй skeleton-заглушки (ProjectCardSkeleton или аналог)
    — Пустое состояние: компонент EmptyState с иконкой и текстом
      "Вакансий не найдено. Попробуйте изменить фильтры."
    — Данные: `positionsApi.getPositions(params)` из api.ts

    Структура состояния страницы:
```tsx
    const [search, setSearch] = useState('');
    const [locationType, setLocationType] = useState<string | undefined>();
    const [expectedLoad, setExpectedLoad] = useState<string | undefined>();
    const [onlyOpen, setOnlyOpen] = useState(true);
    const [page, setPage] = useState(1);
```

16. Зарегистрируй маршрут `/positions` в `src/app/routes.tsx`:
```tsx
    { path: 'positions', Component: PositionsPage }
```
    Маршрут публичный — авторизация не требуется.

───────────────────────────────────────────
БЛОК 5 — НОВЫЙ ФУНКЦИОНАЛ: переход к профилю и его редактирование
───────────────────────────────────────────

17. В Header.tsx в выпадающем меню пользователя (DropdownMenu) уже есть пункт
    "Профиль" → `/profile`. Убедись, что аватар в шапке отображает реальное
    фото пользователя:
    — Загружай профиль текущего пользователя через `useProfileQuery(user.id)`
    — Передавай полученный `avatarUrl` в `<AvatarImage src={avatarUrl} />`
    — Если аватар не загружен — показывай первую букву username как fallback
    — Не блокируй рендер хедера на время загрузки профиля (avatarUrl может
      быть undefined пока грузится)

18. В ProfilePage.tsx кнопка "Редактировать профиль" уже открывает
    `EditProfileDialog`. Убедись, что диалог корректно работает:

    a) EditProfileDialog должен принимать пропсы:
```tsx
       interface EditProfileDialogProps {
         open: boolean;
         onOpenChange: (open: boolean) => void;
         profile: ProfileDTO | undefined;
         onSave: (data: UpdateProfileData) => void;
         isLoading: boolean;
       }
```

    b) Форма внутри диалога должна содержать поля:
       - Отображаемое имя (`display_name`)
       - Специализация (`specialization`)
       - О себе (`bio`) — textarea
       - Навыки (`skills`) — мультиселект или теги (аналогично SettingsPage.tsx,
         компонент уже реализован там — переиспользуй логику)

    c) При открытии диалога предзаполняй поля текущими значениями из `profile`.

    d) Кнопка "Сохранить" вызывает `onSave(data)`, показывает спиннер пока
       `isLoading === true`, после успеха закрывает диалог.

    e) Кнопка "Отмена" закрывает диалог без сохранения и сбрасывает форму
       к исходным значениям.

    f) Используй `updateProfileMutation` из `useUpdateProfileMutation` —
       он уже подключён в ProfilePage.tsx.

19. Добавь в ProfilePage.tsx возможность редактирования навыков прямо на странице
    профиля (не только через Settings):
    — В карточке "Навыки" добавь кнопку-иконку редактирования (иконка `Pencil`
      из lucide-react) рядом с заголовком "Навыки"
    — По клику открывай отдельный диалог (или inline-режим) со списком навыков
      из COMMON_SKILLS (переиспользуй константу из SettingsPage.tsx,
      вынеси её в отдельный файл `src/app/constants/skills.ts`)
    — После сохранения инвалидируй запрос профиля через queryClient

20. Переход к чужому профилю:
    — Страница `/users/:id` (UserProfilePage) уже создана в routes.tsx.
    — Убедись, что она отображает: аватар, отображаемое имя, специализацию,
      bio, список навыков, контакты и список публичных проектов пользователя.
    — На карточке участника команды в ProjectDetailPage (вкладка "Команда")
      клик уже ведёт на `/users/{owner_id}` — проверь, что переход работает.
    — Кнопка "Редактировать профиль" и управление навыками НЕ показываются
      на чужом профиле (сравни `user.id === profileId`).

───────────────────────────────────────────
ДОПОЛНИТЕЛЬНЫЕ ТРЕБОВАНИЯ
───────────────────────────────────────────

- Не меняй структуру файлов и маршрутизацию, кроме явно указанных добавлений.
- Не добавляй новые npm-библиотеки.
- Все тексты интерфейса — на русском языке.
- Поле `password_repeat` в RegisterPage.tsx и api.ts НЕ изменять.
- После каждого исправления убедись, что TypeScript-типы согласованы.
- Вынеси константу COMMON_SKILLS в `src/app/constants/skills.ts` и
  импортируй её в SettingsPage.tsx и ProfilePage.tsx вместо дублирования.
- Ориентируйся на api-docs.md как единый источник истины для структуры
  запросов и ответов.