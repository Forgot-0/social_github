Ты опытный fullstack-разработчик. Перед тобой React/TypeScript-приложение ProjectHub
в директории figma/. Используй api-docs.md как единственный источник истины для API.
Исправь все перечисленные проблемы и реализуй новый функционал.

───────────────────────────────────────────
БЛОК 0 — КРИТИЧЕСКИЕ ОШИБКИ (сборка падает)
───────────────────────────────────────────

1. [КРИТИЧНО] В `src/app/contexts/AuthContext.tsx` вызывается
   `tokenManager.clearTokens()`, которого не существует. В классе `TokenManager`
   есть только `clearAccessToken()`. Исправь вызов на `tokenManager.clearAccessToken()`.

2. [КРИТИЧНО] `src/app/components/PositionCard.tsx` импортирует тип `Position`
   из `../types` (старые моковые типы), а в проекте используется `PositionDTO`
   из `../../api/types`. Перепиши компонент, заменив тип и все поля:
   - `position.requiredSkills` → `position.required_skills`
   - `position.status === 'open'` → `position.is_open`
   - `position.applications.length` → убери (в `PositionDTO` нет поля `applications`)
   - Добавь пропс `projectId?: number` для кнопки "Перейти к проекту"

───────────────────────────────────────────
БЛОК 1 — API / ЛОГИКА
───────────────────────────────────────────

3. [КРИТИЧНО] React Query v5: замени `.isLoading` на `.isPending` во всех мутациях.
   Найди все вхождения в:
   - `EditProjectDialog.tsx` (кнопки Отмена и Сохранить)
   - `PositionDialog.tsx` (обе кнопки)
   - `InviteMemberDialog.tsx` (обе кнопки)
   - `CreateProjectPage.tsx` (кнопка Создать)
   В `useQuery` — `isLoading` оставь как есть.

4. [КРИТИЧНО] `ProfilePage.tsx` обращается к `user?.created_at`, но тип `UserResponse`
   из `api/types.ts` содержит только `{ id, username, email }`. Поле `created_at`
   там не существует. Убери это обращение из отображения или используй
   дату из `profile` объекта если она там есть.

5. [ВАЖНО] Несоответствие типа `avatars` в нескольких местах:
   - В `api/types.ts` определено: `avatars: Record<string, Record<string, string>>`
     (т.е. `avatars['medium']['url']`)
   - В `SettingsPage.tsx` используется: `profile?.avatars?.medium` (как строка)
   - В `ProjectDetailPage.tsx`: `ownerProfile?.avatars?.small` (как строка)
   Исправь все места обращения к `avatars` на корректную форму:
   `profile?.avatars?.['medium']?.['url'] ?? profile?.avatars?.['original']?.['url']`

6. [ВАЖНО] `ApplicationsDialog.tsx` использует `application.decided_at || Date.now()`
   для `formatDistanceToNow`. Но `ApplicationDTO` не имеет `created_at` в типе
   `api/types.ts`. Согласно api-docs.md поле называется `decided_at`.
   Исправь: если `decided_at` равен null — покажи текст "Недавно" без форматирования даты.

7. [ВАЖНО] В `MyProjectsPage.tsx` N+1 запросы: грузятся ВСЕ позиции
   (`usePositionsQuery()` без параметров) и ВСЕ проекты только чтобы сопоставить
   с заявками. Исправь: при получении `myApplications` дополнительно запрашивай
   только нужные проекты по `application.project_id` через
   `useProjectQuery(id)` в подкомпоненте карточки заявки, либо фильтруй
   `usePositionsQuery({ position_id: application.position_id })`.

8. [ВАЖНО] `ProjectDetailPage.tsx` — кнопка "Просмотреть отклики" в блоке
   управления владельца вызывает `handleViewApplications` без аргумента,
   но функция ожидает `PositionDTO`. Исправь: передай `null` и обнови
   `ApplicationsDialog` так, чтобы при `selectedPosition === null` показывались
   все заявки проекта через `useApplicationsQuery({ project_id: projectId })`.

ВАЖНО: поле `repeat_password` в RegisterPage.tsx и связанных файлах НЕ трогать.

───────────────────────────────────────────
БЛОК 2 — ДИЗАЙН / UX
───────────────────────────────────────────

9. HeroBanner: показывай только неавторизованным пользователям. Для авторизованных
   замени на компактный приветственный блок:
   `"Привет, {display_name || username}! Найдите новый проект для себя."`

10. Badge с видимостью проекта в `ProjectCard.tsx` и `MyProjectsPage.tsx`
    показывает "public"/"private" по-английски. Замени:
    `'public' → 'Публичный'`, `'private' → 'Приватный'`

11. В `ProjectDetailPage.tsx` локация и нагрузка позиции показываются как сырые
    английские значения в Badge:
    - `location_type`: `remote → Удалённо`, `onsite → В офисе`, `hybrid → Гибрид`
    - `expected_load`: `low → Низкая`, `medium → Средняя`, `high → Высокая`

12. В `ProjectDetailPage.tsx` нет skeleton при загрузке позиций. Добавь 2–3
    `ProjectCardSkeleton` пока `positionsLoading === true`.

13. Статистика на `HomePage.tsx` захардкожена ("150+", "45"). Скрой карточки
    "Участников" и "Успешных матчей" — показывай только "Активных проектов"
    и "Открытых вакансий" из реальных данных.

───────────────────────────────────────────
БЛОК 3 — НОВЫЙ ФУНКЦИОНАЛ: клик на аватар → профиль
───────────────────────────────────────────

14. В `Header.tsx` сделай так, чтобы клик по аватару переходил на страницу `/profile`:
    - Загружай профиль текущего пользователя: `useProfileQuery(user?.id ?? 0, { enabled: !!user?.id })`
    - Используй полученный `avatarUrl` = `profile?.avatars?.['medium']?.['url']` в `<AvatarImage>`
    - Оберни кнопку-аватар в `<Link to="/profile">` вместо текущего `DropdownMenuTrigger`
    - Dropdown с пунктами (Профиль, Настройки, Выйти) перенеси на отдельную маленькую
      кнопку со стрелкой вниз (иконка `ChevronDown`) рядом с аватаром, ИЛИ
      оставь дропдаун, но добавь `asChild` и оберни `DropdownMenuTrigger` в `<div>`,
      а сам `<Avatar>` при клике ведёт на `/profile` через `onClick={() => navigate('/profile')}`.
    - Пока профиль грузится — показывай первую букву `username` как fallback.

───────────────────────────────────────────
БЛОК 4 — НОВЫЙ ФУНКЦИОНАЛ: просмотр и обработка откликов на позиции
───────────────────────────────────────────

15. Обнови `ApplicationsDialog.tsx` для поддержки двух режимов:
    - `selectedPosition !== null` → показывает заявки на конкретную позицию
      через `usePositionApplicationsQuery(selectedPosition.id)`
    - `selectedPosition === null` → показывает ВСЕ заявки проекта
      через `useApplicationsQuery({ project_id: projectId })`

16. Каждая карточка заявки (`ApplicationCard`) уже имеет кнопки "Принять"/"Отклонить".
    Убедись что они корректно работают:
    - `approveApplicationMutation.mutateAsync(application.id)` → одобрить
    - `rejectApplicationMutation.mutateAsync(application.id)` → отклонить
    - После действия — показывай `toast.success` и инвалидируй запросы заявок
    - Кнопки показывать только если `application.status === 'pending'`
    - Для принятых/отклонённых показывай только Badge со статусом

17. В `ProfilePage.tsx` вкладка "Позиции" уже ведёт на `PositionsTab`.
    `PositionsTab` показывает все позиции платформы — добавь на каждую карточку
    кнопку "Откликнуться" которая вызывает `useApplyToPositionMutation` из
    `api/hooks/usePositions.ts`. Кнопка неактивна если `!position.is_open`.
    После успешного отклика показывай `toast.success('Отклик отправлен!')`.

───────────────────────────────────────────
БЛОК 5 — НОВЫЙ ФУНКЦИОНАЛ: вкладка поиска профилей для приглашения
───────────────────────────────────────────

18. В `ProfilePage.tsx` добавь новую вкладку "Участники" рядом с "Позиции":
```tsx
    <TabsTrigger value="members">Поиск участников</TabsTrigger>
```

19. Создай компонент `src/app/components/MembersSearch.tsx`:
    - Заголовок "Найдите участников для своих проектов"
    - Поиск по `display_name` через `useProfilesQuery({ display_name: search })`
    - Фильтр по навыкам: мультиселект из предустановленного списка навыков
      (переиспользуй `COMMON_SKILLS` из SettingsPage.tsx — вынеси в
      `src/app/constants/skills.ts`)
    - Карточка профиля содержит: аватар, имя, специализацию, список навыков (badges),
      кнопку "Пригласить в проект"
    - Кнопка "Пригласить" открывает маленький диалог с выбором проекта из `useMyProjectsQuery()`
      и роли из `useProjectRolesQuery()`, затем вызывает `useInviteMemberMutation`
    - Пагинация: кнопки Назад/Вперёд
    - Пустое состояние через `EmptyState`

20. Вынеси `COMMON_SKILLS` из `SettingsPage.tsx` в отдельный файл
    `src/app/constants/skills.ts` и импортируй обратно. Также импортируй этот
    файл в `MembersSearch.tsx`, `EditProfileDialog.tsx` и `PositionsTab.tsx`.

───────────────────────────────────────────
БЛОК 6 — НОВЫЙ ФУНКЦИОНАЛ: улучшенная фильтрация позиций с тегами
───────────────────────────────────────────

21. Обнови `PositionsTab.tsx` (и страницу `/positions` если она есть):
    Добавь фильтрацию по навыкам/тегам двумя способами:

    а) **Предустановленные теги** — отображай как кликабельные `Badge` из
       `COMMON_SKILLS` (импортируй из `src/app/constants/skills.ts`).
       По клику добавляй/убираешь тег из `selectedSkills: string[]`.
       Выбранные теги визуально выделены (`variant="default"`), остальные
       (`variant="outline"`).

    б) **Пользовательский тег** — поле `Input` с кнопкой "Добавить".
       При Enter или клике добавляет произвольный навык в `selectedSkills`.
       Добавленные пользовательские теги показываются как Badge с крестиком (×)
       для удаления отдельно от предустановленных.

    в) Передавай `required_skills: selectedSkills` в `usePositionsQuery(params)`.

    г) Показывай счётчик активных фильтров на кнопке "Показать фильтры":
       если фильтры применены — "Фильтры (3)" вместо "Показать фильтры".

    д) Кнопка "Сбросить всё" — сбрасывает поиск, все теги и остальные фильтры.

───────────────────────────────────────────
ДОПОЛНИТЕЛЬНЫЕ ТРЕБОВАНИЯ
───────────────────────────────────────────

- Поле `repeat_password` в RegisterPage.tsx и api/types.ts НЕ изменять.
- Не добавлять новые npm-библиотеки.
- Все тексты интерфейса — на русском языке.
- TypeScript: после каждого изменения проверяй что нет ошибок типов.
- Вынести `COMMON_SKILLS` в `src/app/constants/skills.ts` — сделать это первым делом,
  так как от этого файла зависят другие изменения в блоках 5 и 6.
- Ориентируйся на `src/imports/api-docs.md` как единый источник истины.
- Не трогать структуру файлов и роутинг кроме явно указанных добавлений.