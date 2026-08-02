# Промты для ИИ-вайбкодинга Flutter-клиента (social_github + flutter_riverpod_clean_architecture)

> Основано на: `api-docs.md` (v2.0, полная сверка с бэкендом) + разведка шаблона [ssoad/flutter_riverpod_clean_architecture](https://github.com/ssoad/flutter_riverpod_clean_architecture) (клонирован и прочитан построчно — ниже учтены его реальные, а не предполагаемые конвенции).

## Как этим пользоваться

1. **В контексте ИИ-агента должно быть два файла**: `api-docs.md` (спецификация бэкенда) и этот файл. Промты активно ссылаются на разделы `api-docs.md` — агент должен открывать и перечитывать нужный раздел перед каждым шагом, а не полагаться на память.
2. Промты идут **строго по порядку** (0 → 8) — каждый следующий опирается на слой, созданный предыдущим. Не перескакивать.
3. Каждый промт — самостоятельное сообщение, которое можно скопировать целиком в Claude Code / Cursor / другой агентный инструмент.
4. Инструмент для скаффолдинга — уже встроенный в шаблон `./generate_feature.sh --name <feature>`. Он генерирует папки `domain/data/presentation` и рабочие, но **моковые** (throw-based, без `Either`) заглушки. Каждый промт ниже явно говорит, когда его использовать и как переписать сгенерированное под реальный протокол.
5. Стандарт архитектуры проекта — `docs/CODING_STANDARDS.md` из самого шаблона: **везде `Either<Failure, T>` из `fpdart`, никогда `throw` из репозиториев/юзкейсов; `Notifier`/`AsyncNotifier`, не `StateProvider`; `ref.watch` в build(), `ref.read` в колбэках; DI-провайдеры уровня данных — в `features/<feature>/providers/`, UI-стейт — в `features/<feature>/presentation/providers/`.** Требовать от агента соблюдения этого в каждом промте.
6. ⚠️ Готовые фичи `auth` и `chat` в шаблоне — это **демо-заглушки с фейковыми данными** (`Future.delayed` + захардкоженные объекты, `chat` подключается к публичному echo-серверу `wss://echo.websocket.events`). Слой `domain`/структура — рабочий образец, но весь `data`-слой предстоит переписать на реальные вызовы. Ниже это учтено явно.

---

## Промт 0 — Фундамент: конфигурация, сеть, ошибки, хранилище

```
Контекст: работаем в проекте, склонированном из шаблона ssoad/flutter_riverpod_clean_architecture. Бэкенд полностью описан в приложенном api-docs.md — прочитай целиком разделы 0, 1, 2 и 10 перед началом (это база для всего последующего). Наша задача сейчас — НЕ фичи, а фундамент: сеть, ошибки, хранилище токенов. Все следующие фичи будут строиться на этом слое, поэтому сделай его максимально точным относительно api-docs.md.

Выполни по порядку:

1. Переименование проекта (один раз, в самом начале):
   ./rename_app.sh --app-name "ChatiX" --package-name com.forgot.chatix

2. Добавь в pubspec.yaml зависимости (их нет в шаблоне, но они нужны под нашу специфику API):
   - dio_cookie_manager + cookie_jar — обязательны, потому что refresh-токен бэкенда живёт ТОЛЬКО в HttpOnly-cookie (api-docs.md раздел 3.1, 10.2), без них refresh физически не будет работать
   - flutter_dotenv (или --dart-define, на твой выбор) — для BASE_URL, чтобы не хардкодить

3. lib/core/constants/app_constants.dart:
   - apiBaseUrl должен указывать на реальный бэкенд + суффикс /api/v1 (см. api-docs.md 1.1). Health-check /health — единственный путь БЕЗ этого префикса, учти это в API-клиенте отдельным полем/методом, если понадобится.
   - удали refreshTokenKey и любую идею хранить refresh-токен в SharedPreferences/SecureStorage — он никогда не должен попадать в Dart-код в явном виде (api-docs.md п.5 таблицы расхождений, раздел 10.2). Оставь только accessTokenKey.

4. Перепиши lib/core/error/exceptions.dart и lib/core/error/failures.dart:
   - Добавь ApiFailure extends Failure с полями: String code, String message, dynamic detail (может быть Map<String,dynamic>? или List<dynamic>? — VALIDATION-ошибки отдают detail списком, остальные — объектом или null, см. api-docs.md 2.1–2.2), int status.
   - Добавь RateLimitFailure extends Failure (для 429 — там формат {"detail": "Too Many Requests"}, никакого code/error-конверта, см. api-docs.md 2.2).
   - Сохрани существующие NetworkFailure/TimeoutFailure для сетевых сбоев без ответа сервера.
   - Не удаляй остальные Failure-классы, которыми уже пользуется фича auth — потом решим, оставлять их как алиасы или постепенно вывести из употребления.

5. Перепиши lib/core/network/api_client.dart:
   - Метод _handleError должен разбирать ответ ИМЕННО по формату api-docs.md раздел 2.1: сначала проверить statusCode == 429 → RateLimitFailure(message: response.data['detail']); иначе прочитать response.data['error']['code'], ['message'], ['detail'] → ApiFailure. Если тела нет вообще (обрыв сети) — NetworkFailure/TimeoutFailure как раньше.
   - Учти, что detail для code == "VALIDATION" — список объектов {loc,msg,type}, а для остальных кодов — объект или null; ApiFailure должен просто хранить сырой dynamic, парсинг конкретной формы — забота вызывающего кода.

6. Перепиши lib/core/providers/network_providers.dart (провайдер dio):
   - baseUrl = AppConstants.apiBaseUrl.
   - Подключи PersistCookieJar (dio_cookie_manager) поверх постоянного файлового хранилища (path_provider для доступа к директории приложения) — без этого refresh_token cookie не переживёт перезапуск процесса.
   - Добавь заголовки Content-Type/Accept: application/json по умолчанию, НО помни (и зафиксируй комментарием), что POST /auth/login/ должен отправляться отдельно с Content-Type: application/x-www-form-urlencoded — это будет явно переопределено в auth-фиче (api-docs.md 3.3).
   - Оставь RetryInterceptor как есть, но добавь новый AuthInterceptor (создай файл core/network/interceptors/auth_interceptor.dart) — см. пункт 7.
   - Убедись, что ВСЕ пути, уходящие через этот dio, оканчиваются на "/" — добавь простой интерцептор или helper-функцию buildPath(String path), который гарантирует trailing slash, и договорись, что все datasource-классы будут вызывать через него, а не собирать путь руками (api-docs.md, п.1 таблицы расхождений — 404 без слэша, редиректа не будет).

7. Создай core/network/interceptors/auth_interceptor.dart — QueuedInterceptor:
   - Перед каждым запросом (кроме /auth/login/, /auth/refresh/, /auth/register/... — публичных путей) добавляет заголовок Authorization: Bearer <access_token> из secure storage, если он есть.
   - На onError: если статус 401 (NOT_AUTHENTICATED) или 400 с error.code == "EXPIRED_TOKEN" — поставить запрос в очередь, вызвать POST /auth/refresh/ (без тела, cookie уйдёт сама благодаря cookie_jar), получить новый access_token, сохранить его в secure storage, повторить исходный запрос с новым токеном. Использовать lock (пакет synchronized, он уже есть в pubspec) чтобы параллельные 401 не наплодили несколько refresh одновременно — второй и последующие ждут результата первого.
   - Если refresh тоже упал (400 INVALID_TOKEN/EXPIRED_TOKEN или 404 NOT_FOUND_OR_INACTIVE_SESSION) — почисти secure storage и прокинь оригинальную ошибку дальше (сессия просрочена, дальше это обработает authProvider/router-redirect в промте 1 и 7).
   - 403 INVALID_TOKEN не ретраить через refresh (это невалидный, а не истёкший токен) — сразу считать сессию невалидной.

8. Storage: используй существующие LocalStorageService (некритичные данные) и SecureStorageService (только access_token). Не создавай новых сервисов хранения без необходимости — переиспользуй эти.

9. После всех правок прогони:
   dart run build_runner build --delete-conflicting-outputs
   flutter analyze
   и исправь всё, что аналайзер подсветит.

Ничего из фичевого функционала (экраны, конкретные API-вызовы) в этом промте не делай — только фундамент. В конце коротко перечисли, какие файлы создал/изменил.
```

## Промт 1 — Auth: реальная реализация (регистрация, логин, refresh, verify, reset, OAuth)

```
Контекст: фундамент (dio + cookie jar + AuthInterceptor + ApiFailure) уже готов из промта 0. Открой api-docs.md раздел 3 целиком и держи его перед глазами — ниже переписываем существующую фичу lib/features/auth с моков на реальные вызовы.

ВАЖНО про существующий код: lib/features/auth/data/datasources/auth_remote_data_source.dart сейчас симулирует ответ через Future.delayed и фейковый UserModel — это заглушка-пример, полностью её переписываем. Структуру слоёв (entities/repositories/usecases/data) СОХРАНЯЕМ, меняем содержимое.

1. domain/entities/user_entity.dart — замени поля на то, что реально отдаёт бэкенд. У API нет единой сущности "User" с одинаковым набором полей везде (api-docs.md 3.2, 3.9, 3.11) — сделай так:
   - UserEntity (лёгкая, из /register и /me): id (int), username (String), email (String).
   - Отдельно заведи (если нужно на будущее для профиля/админки) UserDetailEntity с roles/permissions/sessions — но не обязательно сейчас, будет не нужен до появления админ-экранов.

2. data/models/user_model.dart — под точную форму UserResponse {id, username, email} (api-docs.md 3.2, 3.9). fieldRename оставь snake_case только если реально нужно — тут поля и так плоские.

3. domain/repositories/auth_repository.dart — перепроектируй интерфейс под реальные операции:
   - Future<Either<Failure, UserEntity>> register({required String username, required String email, required String password, required String passwordRepeat})
   - Future<Either<Failure, void>> login({required String username, required String password})  // username — единое поле логина, см. api-docs.md 3.3, НЕ email/password по отдельности как в моке; login не возвращает UserEntity напрямую — только access_token, поэтому дальше нужен отдельный getCurrentUser()
   - Future<Either<Failure, void>> logout()
   - Future<Either<Failure, UserEntity>> getCurrentUser()  // GET /users/me/
   - Future<Either<Failure, void>> requestEmailVerification({required String email})
   - Future<Either<Failure, void>> confirmEmailVerification({required String token})
   - Future<Either<Failure, void>> requestPasswordReset({required String email})
   - Future<Either<Failure, void>> confirmPasswordReset({required String token, required String password, required String passwordRepeat})
   - Future<Either<Failure, String>> getOAuthUrl({required String provider, bool connect = false})  // возвращает url для открытия в браузере/WebView

4. data/datasources/auth_remote_data_source.dart — реальные вызовы через Dio (получай его из dioProvider):
   - register → POST /users/register/ (JSON) — точные поля и правила валидации пароля бери из api-docs.md 3.2 (8-128 симв., верхний+нижний регистр+цифра+спецсимвол — это должно быть продублировано и на клиенте для мгновенной обратной связи в форме, до похода в сеть)
   - login → POST /auth/login/ — ОБЯЗАТЕЛЬНО Content-Type: application/x-www-form-urlencoded, тело — FormData/Options с полями username и password (НЕ JSON). Ответ — только {access_token}, сохрани его в SecureStorageService сразу здесь же в datasource или чуть выше в repository — обсуди сам, где логичнее, но сделай последовательно с остальными методами.
   - logout → POST /auth/logout/ (без тела), после успеха — удалить access_token из secure storage.
   - getCurrentUser → GET /users/me/
   - requestEmailVerification → POST /auth/verifications/email/ {email}
   - confirmEmailVerification → POST /auth/verifications/email/verify/ {token}
   - requestPasswordReset → POST /auth/password-resets/ {email}
   - confirmPasswordReset → POST /auth/password-resets/confirm/ {token, password, password_repeat}
   - getOAuthUrl → GET /auth/oauth/{provider}/authorize/ или /authorize/connect/ (если connect=true) — provider ∈ google|yandex|github

5. data/repositories/auth_repository_impl.dart — прокидывает вызовы датасорса, ловит ApiFailure/RateLimitFailure/NetworkFailure из api_client и возвращает Either. Никакого сохранения "user data" в LocalStorageService как в старом моке не нужно — источник правды всегда GET /users/me/, локально кешируем по минимуму (например, последний известный UserEntity для мгновенного отображения UI, но с ревалидацией).

6. domain/usecases/ — обнови LoginUseCase/RegisterUseCase/LogoutUseCase под новую сигнатуру репозитория, добавь новые usecases: RequestEmailVerificationUseCase, ConfirmEmailVerificationUseCase, RequestPasswordResetUseCase, ConfirmPasswordResetUseCase, GetOAuthUrlUseCase, GetCurrentUserUseCase. Валидацию пустых полей (как было в LoginUseCase) сохрани в духе существующего стиля.

7. presentation/providers/auth_provider.dart — AuthController (AsyncNotifier или Notifier с состоянием AsyncValue<UserEntity?>):
   - На старте приложения (build()) проверяет наличие access_token в secure storage → если есть, дёргает getCurrentUser(); если 401/403 — токен невалиден, состояние = неавторизован (interceptor уже попытался refresh — если и это не помогло, значит сессии действительно нет).
   - login(), register(), logout() как методы, после успешного логина/регистрации сразу подгружают getCurrentUser() и обновляют состояние.
   - Отдельно вынеси boolean-геттер isAuthenticated для роутера (промт 7).

8. presentation/screens/login_screen.dart и register_screen.dart — используй flutter_form_builder + form_builder_validators (уже в pubspec, в шаблоне их пока нигде не используют, но это стандартный путь для форм в этом стеке). Поле логина назвать "username" в форме (но подсказать пользователю, что это email или юзернейм — бэкенд принимает то же поле для обоих, уточнить в api-docs.md 3.3, если не уверен — считать что это одно текстовое поле). Добавь клиентскую валидацию пароля по тем же правилам, что и на бэке, чтобы не тратить запрос впустую.

9. Новые экраны (создай presentation/screens/):
   - verify_email_screen.dart — поле для ввода токена (или прими токен из deep link/query-параметра, если реализуешь диплинки — не обязательно в этом промте), кнопка "отправить письмо повторно" (rate limit 3/час, обработай 429 отдельно — покажи "попробуйте позже").
   - reset_password_request_screen.dart — email → запрос кода.
   - reset_password_confirm_screen.dart — token + новый пароль + повтор.
   - oauth_buttons (виджет) — три кнопки google/yandex/github, по нажатию получают url через getOAuthUrl и открывают его через url_launcher (уже в pubspec) во внешнем браузере. Callback-обработку (получение access_token после OAuth) в этом промте зафиксируй как TODO с комментарием — точная механика зависит от настроенного backend redirect_uri (см. api-docs.md 3.8, там это тоже отмечено как открытый вопрос) и потребует либо deep link, либо WebView — не изобретай точную схему сам, оставь заглушку и явно предупреди об этом в саммари.

10. Обнови lib/core/router/app_router.dart минимально — пока не про полноценную схему роутинга (это промт 7), а только чтобы новые экраны (verify/reset) были доступны по путям и existing redirect-логика на основе authProvider.isAuthenticated продолжала работать.

11. Тесты по образцу test/features/auth/domain/usecases/login_use_case_test.dart — как минимум для LoginUseCase, RegisterUseCase, GetCurrentUserUseCase (mocktail + Either-assertions).

В конце — краткое резюме изменённых файлов и явный список того, что осталось как TODO (в первую очередь OAuth callback).
```

## Промт 2 — Профили (`/profiles`)

```
Контекст: auth-слой (access-токен в secure storage, AuthInterceptor, dio) уже готов и работает. Открой api-docs.md раздел 4 целиком.

1. Сгенерируй скелет: ./generate_feature.sh --name profile
   Сгенерированный код использует @riverpod codegen и НЕ использует Either (кидает исключения). Приведи его к стандарту проекта (docs/CODING_STANDARDS.md) — перепиши repository/usecases на Either<Failure, T> из fpdart, как сделано в features/auth, а не оставляй как из коробки сгенерировал скрипт.

2. domain/entities/profile_entity.dart — под ProfileDTO (api-docs.md 4.3):
   id, avatars (Map<String, Map<String,String>> — ключи размеров "32"/"64"/"256"/"512", внутри "jpg"/"webp"/"avif"), specialization, displayName, bio, dateBirthday, skills (List<String> или Set<String>), contacts (List<ContactEntity>{profileId, provider, contact}).
   Добавь на entity вспомогательный геттер вроде String? bestAvatarUrl(int preferredSize) — который берёт ближайший доступный размер и предпочитает webp→jpg→avif (или другой практичный порядок), чтобы виджеты профиля не дублировали эту логику. avatars может быть пустым объектом {} — обработай как "аватара нет".

3. domain/repositories/profile_repository.dart:
   - Future<Either<Failure, PageResult<ProfileEntity>>> getProfiles({String? username, String? displayName, List<String>? skills, int page = 1, int pageSize = 20, String? sort})
   - Future<Either<Failure, ProfileEntity>> getProfile(int profileId)
   - Future<Either<Failure, void>> updateProfile(int profileId, {String? specialization, String? displayName, String? bio, List<String>? skills, DateTime? dateBirthday})
   - Future<Either<Failure, AvatarPresignEntity>> presignAvatar({required String filename, required int size, required String contentType})
   - Future<Either<Failure, void>> completeAvatarUpload({required String keyBase, required int size, required String contentType})
   - Future<Either<Failure, void>> addContact(int profileId, {required String provider, required String contact})
   - Future<Either<Failure, void>> removeContact(int profileId, {required String provider})

   Заведи общий переиспользуемый generic-класс PageResult<T> (core/network или core/models — реши, где логичнее один раз, дальше все остальные фичи будут его переиспользовать) СТРОГО с 4 полями items/total/page/pageSize и посчитанными на клиенте геттерами totalPages/hasNext/hasPrevious (api-docs.md раздел 1.5 и п.3 таблицы расхождений — на сервере этих полей в JSON нет).

4. data/datasources/profile_remote_data_source.dart — точные пути (не забывай слэш в конце везде):
   - GET /profiles/ (публичный, без токена — но раз AuthInterceptor у нас навешивает Authorization если токен есть, ничего страшного, эндпоинт работает и с токеном, и без)
   - GET /profiles/{id}/
   - PUT /profiles/{id}/ — именно PUT, не PATCH (api-docs.md 4.4)
   - POST /profiles/avatar/presign/ → {url, fields, key_base}
   - POST /profiles/avatar/upload_complete/
   - POST /profiles/{id}/contacts/
   - DELETE /profiles/{id}/{provider}/delete/ — обрати внимание на форму пути: она НЕ /contacts/{provider}/, а именно /{id}/{provider}/delete/ (api-docs.md 4.6)

5. Загрузка аватара — САМОЕ важное место фичи, сделай отдельный use case UploadAvatarUseCase, который инкапсулирует все 3 шага (api-docs.md 4.5):
   a) presignAvatar(filename, size, contentType) → получить url/fields/key_base
   b) СЫРОЙ multipart POST-запрос НАПРЯМУЮ на presigned url из шага (a), с полями из fields как есть плюс сам файл под ключом "file" — это отдельный dio-запрос МИМО нашего основного ApiClient/dio с Authorization-интерцептором (presigned URL не должен получать наш Bearer-токен, он идёт напрямую в S3/MinIO с собственной подписью в fields). Прими на вход File/Uint8List и контент-тайп/имя файла.
   c) completeAvatarUpload(keyBase, size, contentType)
   Верни из use case что-то вроде AsyncValue-совместимый прогресс (хотя бы этапы enum: presigning/uploading/confirming/done), чтобы экран мог показать прогресс-индикатор.

6. presentation — экран профиля (просмотр чужого/своего), экран редактирования (форма через flutter_form_builder — specialization/displayName/bio/skills-чипы/dateBirthday), виджет выбора и загрузки аватара (image_picker потребуется — добавь в pubspec, в шаблоне его нет). Список профилей — переиспользуй паттерн PageResult+пагинации, который сложится тут как образец для остальных списковых фич (проекты/позиции/уведомления будут выглядеть аналогично).

7. Учти правило доступа на клиенте: PUT/contacts разрешены только если profileId == текущий пользователь ИЛИ у него есть системные права (сейчас у нас нет UI для системных прав — просто скрывай кнопку "редактировать" на чужих профилях, api-docs.md 4.4).

Тесты для usecases по аналогии с промтом 1.
```

## Промт 3 — Проекты (`/projects`, `/positions`, `/applications`, `/project_roles`)

```
Контекст: слой профилей и переиспользуемый PageResult<T> из промта 2 уже есть. Открой api-docs.md раздел 5 и раздел 9.2 (матрица прав проекта) целиком.

Это самая крупная REST-фича — можно сделать её как одну фичу "projects" с несколькими под-модулями (positions/applications внутри неё), либо как несколько отдельных фич через generate_feature.sh (project, position, application). Выбери один вариант и будь последователен; рекомендация — одна фича "project" с datasource-ами, разбитыми на отдельные файлы project_remote_data_source.dart / position_remote_data_source.dart / application_remote_data_source.dart внутри общего data/datasources/, потому что домены сильно переплетены (позиция принадлежит проекту, заявка — позиции).

1. Entities (domain/entities/): ProjectEntity, ProjectMemberEntity, PositionEntity, ApplicationEntity, ProjectRoleEntity — поля бери 1:1 из api-docs.md 5.1–5.5. Обрати внимание:
   - в ProjectEntity поле называется fullDescription (а не description) — бэкенд при ЗАПРОСЕ принимает description, а при ОТВЕТЕ отдаёт full_description; сделай это явным комментарием в модели/мэппере, это частая точка ошибок.
   - visibility — enum с тремя значениями private/internal/public (не два).
   - ProjectMemberEntity.status — enum invited/pending/active/suspended/removed (не путать с ApplicationEntity.status — pending/accepted/rejected, это другой enum на другой сущности).
   - PositionEntity.locationType — remote/onsite/hybrid, expectedLoad — low/medium/high.

2. Repository-интерфейс (domain/repositories/project_repository.dart) — весь список операций из api-docs.md таблиц 5.1–5.5:
   createProject, getProjects(filters), getMyProjects, getProject(id), updateProject, deleteProject,
   inviteMember, acceptInvite, getMyInvites (⚠️ путь /profiles/invites/my/, а не /projects/... — см. ниже), changeMemberRole, updateMemberPermissions,
   createPosition, getProjectPositions, getPositions(filters), getPosition(id), updatePosition, deletePosition,
   getPositionApplications, applyToPosition,
   getApplications(filters), getMyApplications, approveApplication, rejectApplication,
   getProjectRoles.

3. Datasource — точные пути из api-docs.md 5.1–5.5, включая:
   - POST /projects/{id}/invite/, POST /projects/{id}/members/accept/, POST /projects/{id}/members/{userId}/role/, PUT /projects/{id}/members/{userId}/permissions/
   - GET /profiles/invites/my/ — ⚠️ ЭТО НЕ ОПЕЧАТКА В ЭТОМ ПРОМТЕ, так на самом деле роутит бэкенд (баг роутинга на сервере, задокументирован в api-docs.md п.7 таблицы расхождений и в 5.2). Вызывай именно этот путь, даже если по смыслу он про проекты.
   - GET /positions/ и GET /positions/{id}/ — публичные (без токена), но остальные операции с позициями требуют авторизации.
   - GET /project_roles/ — публичный, read-only, никаких POST/PUT для ролей проекта нет вообще (это не забытая фича, а так и задумано на бэке).

4. UseCases — по одному на операцию (или сгруппируй логически, но придерживайся уже устоявшегося в auth/profile стиля одного usecase на одно действие).

5. Presentation:
   - Экран списка проектов (публичный доступ к чтению не нужен — API требует авторизации почти везде в этом модуле, в отличие от profiles/positions) с фильтрами по тегам/имени.
   - Экран "Мои проекты" (/projects/my/).
   - Экран деталей проекта — вкладки: инфо, участники (с ролями из матрицы 9.2 и возможностью сменить роль/права, если у текущего пользователя есть member:invite/member:udpate — да, в API опечатка "udpate", у нас в Dart-коде называть поле нормально, просто отправлять/сверять со строкой "member:udpate" как есть при работе с правами роли), позиции.
   - Экран "Мои приглашения" (список из getMyInvites) с кнопкой "принять".
   - Экран деталей позиции + кнопка "откликнуться" (форма с необязательным полем message).
   - Экран "Мои заявки" (по статусам).
   - Для владельца/мейнтейнера позиции — список заявок на позицию с approve/reject.
   - Реализуй прикладной helper hasProjectPermission(ProjectMemberEntity? me, String permission) — читает me.role.permissions[permission] == true, используй его для условного показа кнопок управления (см. полную матрицу в api-docs.md 9.2, и общий принцип видимости UI в 10.6).

6. Лимиты, которые стоит проверять на клиенте ДО отправки запроса (чтобы не тратить круг на 400): максимум 3 проекта на пользователя, максимум 5 открытых позиций на проект (api-docs.md 5.1, 5.3) — если знаешь текущее количество (из getMyProjects/getProjectPositions), можно заранее дизейблить кнопку "создать" с подсказкой, но финальную проверку всё равно делает сервер — обработай MAX_PROJECTS_LIMIT_EXCEEDED/MAX_POSITIONS_PER_PROJECT_LIMIT_EXCEEDED как обычную ApiFailure с понятным текстом.

Тесты — как минимум для createProject/inviteMember/applyToPosition/approveApplication usecases.
```

## Промт 4 — Чаты: REST-слой (без реалтайма — это следующий промт)

```
Контекст: в этом промте намеренно делаем ТОЛЬКО REST-часть чатов (список чатов, история сообщений, отправка, участники, вложения, звонки) — WebSocket-слой и живое обновление сообщений будет отдельным промтом 5, который достроит этот же фичемодуль. Открой api-docs.md разделы 6 (весь) и 9.1 (матрица прав чата) целиком.

Существующая фича lib/features/chat в шаблоне — демо-пример с подключением к публичному echo-серверу wss://echo.websocket.events и плоской моделью MessageModel{text}. Структуру каталогов (data/domain/presentation/providers) переиспользуем, содержимое полностью переписываем. В этом промте НЕ трогай chat_remote_data_source.dart в части WebSocket (это промт 5) — добавь рядом REST-специфичный источник данных.

1. Entities (domain/entities/): ChatEntity, ChatMemberEntity, MessageEntity, AttachmentEntity, CallTokenEntity. Поля — 1:1 с ChatDTO/ChatDetaiDTO/MemberChatDTO/MessageDTO/AttachmentDTO/JoinTokenDTO из api-docs.md 6.2–6.6. Учти:
   - ChatEntity.type — enum direct/group/supergroup/channel (4 значения, не 3).
   - AttachmentEntity.attachmentStatus — enum pending/success/error.
   - MessageEntity должна поддерживать вложенные replyTo/forwardedFrom (тот же тип MessageEntity, может быть null) и список attachments.

2. Для списков чатов/сообщений/участников — это КУРСОРНАЯ пагинация, НЕ PageResult<T> из промта 2 (api-docs.md 1.6, 6.2–6.4)! Заведи отдельные обёртки:
   - ChatsPage { List<ChatEntity> chats; bool hasNext; String? nextDate; String? nextChatId; }
   - MessagesPage { List<MessageEntity> messages; int? nextCursor; bool hasNext; }
   - MembersPage { List<ChatMemberEntity> members; bool hasNext; int? nextUserId; List<MemberPresenceEntity> presence; }
   Тут hasNext — реальное поле из ответа, не считается на клиенте (в отличие от PageResult<T>).

3. Repository (domain/repositories/chat_repository.dart):
   getChats({int limit = 50, String? lastChatId, DateTime? lastActivityAt}),
   createChat({name?, description?, chatType, memberIds, isPublic, adminOnly, slowModeSeconds, permissions}),
   getChat(chatId), updateChat(chatId, {...}), deleteChat(chatId), joinChat(chatId), leaveChat(chatId),
   getMembers(chatId, {limit, cursorUserId, includePresence}), addMember(chatId, userId, roleId), changeMemberRole(chatId, userId, roleId), banMember(chatId, userId, {reason?, bannedTo?}), kickMember(chatId, userId),
   getMessages(chatId, {limit, cursorMessageSeq}), getMessagesContext(chatId, targetSeq, {limit}), sendMessage(chatId, {content?, replyToId?, messageType?, uploadTokens?, idempotencyKey?}), getMessage(chatId, messageId), editMessage(chatId, messageId, content), deleteMessage(chatId, messageId), forwardMessage({sourceChatId, sourceMessageId, targetChatId, comment?}), markRead(chatId, messageSeq),
   requestAttachmentUpload(chatId, uploads), confirmAttachmentUpload(chatId, uploadTokens), getAttachmentDownloadUrl(chatId, messageId, attachmentId),
   joinCall(chatId), muteCallParticipant(chatId, userId, muted).

4. Datasource — точные пути и нюансы из api-docs.md:
   - PATCH /chats/{id}/ (не PUT!) для обновления настроек чата.
   - Для создания direct-чата (chatType="direct") memberIds ДОЛЖЕН содержать РОВНО один id — проверь на клиенте перед отправкой и покажи понятную ошибку, а не жди 400 с сервера.
   - PATCH /chats/{chat_id}/members/{user_id}/ban/ — тело {reason?, banned_to?} — да, поле называется banned_to (опечатка в реальном API), назови Dart-параметр нормально (bannedTo), но при сериализации в JSON ключ должен быть именно "banned_to".
   - sendMessage — поддержи заголовок Idempotency-Key (сгенерируй uuid на клиенте перед каждой отправкой пакетом v4 из пакета uuid, который уже в pubspec) — это важно для сценария "нет сети → пользователь жмёт отправить ещё раз при реконнекте", чтобы не задублировалось сообщение (api-docs.md 6.4).
   - Вложения — ДВА отдельных HTTP-вызова вне основного Bearer-потока, аналогично аватару из промта 2, но другой механизм: шаг 2 это PUT сырых байт файла на upload_url (НЕ multipart POST, как было у аватара!) — сделай отдельный UploadChatAttachmentUseCase, который: (a) requestAttachmentUpload → список {upload_token, upload_url, attachment_type, expires_in}; (b) для каждого файла — PUT на upload_url с Content-Type файла и телом = сырые байты (dio.put с data: File как Stream или bytes, без всякого MultipartFile); (c) confirmAttachmentUpload(uploadTokens) → 202, дальше готовность вложений прилетит через WebSocket-событие attachment_success в промте 5 — в этом промте просто сохрани, что «после confirm можно сразу пробовать sendMessage с этими же upload_tokens» согласно api-docs.md 6.5.
   - Ограничения загрузки проверяй на клиенте ДО начала: изображения/видео ≤50МБ и максимум 10 шт., обычные файлы ≤100МБ и максимум 1 шт. на сообщение, разрешённые MIME — списком из api-docs.md 6.5 (используй их, чтобы фильтровать file_picker/image_picker).

5. Presentation:
   - Список чатов (курсорная подгрузка по скроллу — infinite list с ChatsPage.nextChatId/nextDate).
   - Экран чата — лента сообщений (пока БЕЗ живого обновления, только пул-ту-рефреш/пагинация по MessagesPage — реалтайм добавим в промте 5), поле ввода, прикрепление файлов, ответ/пересылка.
   - Экран участников с ролями/баном/киком, видимость кнопок — по матрице прав api-docs.md 9.1 (аналогично helper из промта 3, но для chat.permissions/memberChatDTO.permissionsOverrides — учти, что итоговое право — это объединение: базовая роль → override чата → персональный override участника, слияние делает бэкенд, но для показа/скрытия UI-кнопок используй ту же логику на клиенте по последним полученным данным).
   - Кнопка "Позвонить" — получает JoinTokenDTO и просто выводит токен/URL на экран как заглушку (полноценная интеграция с LiveKit SDK — по желанию, вне рамок этого промта; если решишь делать сразу, добавь пакет livekit_client и подключись к комнате через token+livekit_url).

Тесты — для sendMessage/createChat/requestAttachmentUpload usecases минимум.
```

## Промт 5 — Чаты: WebSocket-слой (реалтайм)

```
Контекст: REST-часть чатов из промта 4 готова и работает. Открой api-docs.md раздел 7 (весь, это самый подробный раздел документа) и раздел 10.5 — прочитай медленно, протокол нетривиальный. Это самый важный промт всего набора для UX приложения.

Существующий lib/features/chat/data/datasources/chat_remote_data_source.dart (демо на echo-сервере) — используй только как отправную точку по структуре (Stream<T> + StreamController.broadcast + connect/disconnect), протокол внутри перепиши полностью с нуля.

1. Создай core/websocket/chat_socket_service.dart (это специфично для чата, но лучше не прятать внутри features/chat/data, а сделать сервис уровня core, потому что WS-соединение — синглтон на всё приложение, а не per-screen) со следующим публичным API:
   - Future<void> connect() — собирает URL {baseWsUrl}/chats/ws/?token=<access_token из secure storage>, опционально device_id.
   - Stream<WSEvent> get events — общий broadcast-стрим всех входящих доменных и служебных событий (см. п.2).
   - void subscribe(String chatId, {int? lastSeq})
   - void unsubscribe(String chatId)
   - void resume(Map<String, int> cursors) — САМ проверяет, что cursors.length <= 20, если больше — бери только 20 самых свежих (например по last-viewed), не отправляй как есть (api-docs.md 7.3, риск обрыва соединения при MAX_LIMIT_CURSOR).
   - Внутренняя логика heartbeat: слушать ws.ping от сервера, отвечать {"op":"pong"} на каждый; если 75 секунд (бери из значения ws.ready.payload.heartbeat_timeout, не хардкодь) нет собственной активности — можно проактивно послать {"op":"ping"} самому, чтобы не полагаться только на серверный пуш.
   - Автопереподключение с экспоненциальным backoff (например 1с/2с/4с/8с/макс 30с) при любом закрытии, кроме намеренного disconnect() от нас. После реконнекта — НЕ просто заново subscribe на всё подряд, а resume() с последними известными (chatId → lastSeq) для чатов, которые сейчас видны в UI/были подписаны.
   - Обработка close-кодов: 1001 (heartbeat timeout) и 1012 (connection limit exceeded, вытеснили третьим подключением) — не ошибка пользователя, просто тихо переподключиться; 1008 (missing/bad token) — не переподключаться автоматически, это значит access_token невалиден, дать сигнал наверх (через тот же events-стрим специальным внутренним событием или через отдельный ValueNotifier<bool> isTokenInvalid) чтобы вызвать logout/refresh.

2. Модель события — freezed union (sealed class) под ВСЕ типы из api-docs.md 7.4, не забудь ни одного:
   Доменные: NewMessage, MessageEdited, MessageDeleted, MessagesRead, MemberJoined, MemberLeft, MemberKick, MemberBanned, ChatCreated, ChatUpdated, AttachmentSuccess, ChatDeleted (⚠️ единственное, у которого type в сыром виде "chats.chat.deleted", а не "красивое" имя — обработай это как частный случай в парсере, см. api-docs.md 7.4 таблицу).
   Служебные: WsReady, WsSubscribed, WsUnsubscribed, WsHistory, WsPong, WsPing, WsErrorBadCommand (code, detail — без ts/payload), WsErrorNotChatMember (code, ts — без detail/payload).
   Обязательно учти, что у двух вариантов ws.error РАЗНАЯ форма полей (api-docs.md 7.4) — не пытайся впихнуть в одну универсальную структуру с обязательными полями, сделай парсинг по code внутри.
   Парсер "raw JSON → WSEvent" разбирай по полю type, с fallback-веткой на неизвестный type (просто заворачивай в Unknown(raw) и логируй, не крашь приложение на новых/незнакомых событиях от бэкенда).

3. ⚠️ КЛЮЧЕВОЕ архитектурное решение, не пропусти — из api-docs.md 7.4/7.5: события new_message/message_edited/message_deleted несут ТОЛЬКО {message_id, seq, ...}, БЕЗ содержимого сообщения. Правильная схема:
   - При получении NewMessage(messageId, seq, chatId) — если это чат, открытый прямо сейчас на экране, дозапросить GET /chats/{chatId}/messages/{messageId}/ (или просто рефетчить последнюю страницу через уже готовый getMessages из промта 4) и вставить в локальный стейт сообщений этого чата.
   - Если это НЕ открытый сейчас чат — просто увеличить unread_count/обновить last_activity в локальном списке чатов (ChatEntity), не тратясь на дозапрос полного сообщения, пока пользователь не откроет чат.
   - Своё же только что отправленное сообщение НЕ дозапрашивать повторно по WS-событию — оно уже добавлено в стейт оптимистично сразу после успешного ответа REST-вызова sendMessage (избегай дублирования по message_id при мёрже).
   - MessageEdited/MessageDeleted — аналогично, точечно обновить/удалить конкретное сообщение в локальном стейте по messageId (для edited — дозапросить актуальный content, для deleted — просто убрать или пометить как удалённое).

4. Интеграция с Riverpod (presentation/providers/chat_socket_provider.dart или рядом с существующим chat_provider.dart):
   - Провайдер, который держит ChatSocketService как синглтон и подключается один раз при первом логине (слушай authProvider.isAuthenticated — при true подключай сокет, при false — отключай и очищай подписки).
   - ChatMessagesController (per-chatId AsyncNotifier/family-провайдер) — при открытии экрана чата вызывает getMessages (REST, из промта 4) для начальной загрузки И socketService.subscribe(chatId, lastSeq: <seq последнего известного сообщения>), слушает events-стрим, фильтрует по своему chatId, мёржит доменные события в свой список сообщений по правилам из п.3. При закрытии экрана — socketService.unsubscribe(chatId) (dispose провайдера).
   - ChatsListController — слушает те же события (member_joined и т.п. не так важны здесь, важнее chat_created/chat_updated/new_message-для-непросматриваемых-чатов/messages_read) чтобы обновлять список чатов и бейджи непрочитанного без полного рефетча.
   - AttachmentSuccess-событие — если у пользователя открыт экран составления сообщения с ожидающими вложениями (по upload_token из payload.tokens), разблокировать кнопку "отправить"/убрать спиннер загрузки конкретного вложения.

5. Presentation-детали: индикатор состояния соединения (например маленькая точка/баннер "переподключение...") на экране чата, построенный на стриме статусов от ChatSocketService (добавь туда Stream<ChatSocketStatus> где ChatSocketStatus = connecting/ready/reconnecting/disconnected).

6. Не реализовывай обработку typing_start/typing_stop/call_started/call_ended/call_joined/call_left как что-то, что реально придёт от сервера — согласно api-docs.md 7.4 эти типы объявлены, но бэкенд их не шлёт. Можно завести на них пустые ветки в sealed-классе на будущее, но не строить вокруг них функциональность (например "печатает..." индикатор) — она не будет работать, пока бэкенд не начнёт эти события слать.

Тесты: для парсера JSON→WSEvent (особенно двух форм ws.error и частного случая chats.chat.deleted) — юнит-тесты без реального сокета, просто на функции парсинга.
```

## Промт 6 — Уведомления (`/devices`, `/notifications`)

```
Контекст: открой api-docs.md раздел 8 целиком (он короткий). В шаблоне уже есть абстракция lib/core/notifications/notification_service.dart (NotificationService с init/requestPermission/getToken/notificationStream и т.д.) — она про ПОЛУЧЕНИЕ push через FCM/APNs на устройстве, у нас нет готовой реализации (только интерфейс + debug-заглушка debug_notification_service.dart), полноценную интеграцию с Firebase Cloud Messaging делать не обязательно в рамках этого промта (это отдельная большая настройка Firebase-проекта), но структуру подготовь так, чтобы это подключалось позже без переделок.

1. Сгенерируй фичу: ./generate_feature.sh --name notification (аналогично промту 2 — переведи сгенерированный код на Either).

2. domain/entities/notification_entity.dart — под NotificationDTO (api-docs.md 8.2): id, userId, type (enum system/project/chat), title, message, payload (Map<String,dynamic> — трактуй defensively, единой строгой схемы на бэке нет), isRead, createdAt, updatedAt.

3. domain/repositories/notification_repository.dart:
   - Future<Either<Failure, void>> registerDevice({required String platform, required String token, required String deviceName}) — platform строго одно из "IOS"/"WEB"/"ANDROID" (заглавными буквами, как в api-docs.md 8.1, не платформозависимый Platform.isIOS/isAndroid просто как есть — преобразуй явно в эти строки).
   - Future<Either<Failure, PageResult<NotificationEntity>>> getNotifications({bool? isRead, int page = 1, int pageSize = 20, String sort = "created_at:desc"}) — это снова обычный PageResult<T> из промта 2 (page-based, не курсорный, как чаты).
   - Future<Either<Failure, int>> getUnreadCount()
   - Future<Either<Failure, void>> markAsRead(int notificationId, {bool isRead = true})
   - Future<Either<Failure, int>> markAllAsRead() — ⚠️ ответ сервера это ГОЛОЕ число (сколько уведомлений отмечено), не объект — учти при парсинге JSON в datasource (просто `int.parse(response.data.toString())` или `response.data as int`, в зависимости от того, как Dio его отдаст).

4. Datasource — POST /devices/, GET /notifications/, GET /notifications/unread_count/, PATCH /notifications/{id}/read/, PATCH /notifications/read_all/.

5. Регистрация устройства: вызывай registerDevice сразу после успешного логина (интегрируй в AuthController.login() из промта 1 — после getCurrentUser() дополнительно попробуй notificationService.getToken() → если не null, зарегистрируй его через registerDevice; если push ещё не настроен (getToken() вернёт null/бросит — используется DebugNotificationService), просто пропусти без ошибки пользователю, это не блокирующая операция).

6. Presentation:
   - Иконка колокольчика с бейджем непрочитанных (провайдер, который держит unreadCount и обновляет его периодически/по pull-to-refresh — WS-события на уведомления бэкенд не шлёт, значит только поллинг или обновление при открытии экрана/возврате в foreground, не полагайся на реалтайм здесь).
   - Экран списка уведомлений с пагинацией, тап по уведомлению — markAsRead + переход по релевантному экрану, если из payload можно понять цель (например payload.chat_id → открыть чат, payload.project_id → открыть проект — сделай это best-effort/defensive, не крашь если полей нет).
   - Кнопка "прочитать все".

Тесты для getNotifications/markAllAsRead usecases.
```

## Промт 7 — Навигация, shell, RBAC-видимость в UI

```
Контекст: все фичи (auth/profile/project/chat/notification) из промтов 1–6 реализованы. Открой api-docs.md разделы 9 (целиком) и 10.6. Задача этого промта — собрать их в цельное приложение с адекватной навигацией и правами доступа в UI, а не плодить новую бизнес-логику.

1. Перепиши lib/core/router/app_router.dart на go_router с ShellRoute для основного каркаса (нижняя навигация: Чаты / Проекты / Уведомления / Профиль) поверх плоских маршрутов для остального (детали проекта, чат, редактирование профиля и т.д.). Сохрани существующий паттерн redirect на основе authProvider (api-docs.md логика не меняется, только теперь isAuthenticated берётся из переписанного в промте 1 AuthController), но расширь набор публичных путей на login/register/verify-email/reset-password/oauth-callback (если реализован).

2. Заведи типизированные маршруты (go_router 17 поддерживает как минимум путь с параметрами) для: /chats/:chatId, /projects/:projectId, /projects/:projectId/positions/:positionId, /profiles/:profileId, /notifications — с корректной передачей ID в соответствующие провайдеры/контроллеры (family-провайдеры из промтов 2–5).

3. Централизуй RBAC-геттеры из промтов 3–4 (hasProjectPermission, hasChatPermission) в общий lib/core/rbac/permission_helpers.dart, если раньше они были размазаны по фичам — так они переиспользуются в AppBar-экшенах/меню одинаково на разных экранах.

4. Обработай сценарий "сессия истекла посреди работы": если AuthInterceptor (промт 0) не смог обновить токен и вернул ошибку сессии — AuthController должен перейти в неавторизованное состояние, роутер должен САМ сделать redirect на /login (через существующий redirect-колбэк, реагирующий на authProvider), не полагайся на то, что экран сам поймает 401 и вручную вызовет навигацию — это должно работать из любого места приложения одинаково.

5. Пустые/лоадинг/error-состояния — пройдись по всем спискам (чаты/проекты/позиции/уведомления/участники) и убедись, что везде единообразно показывается: skeleton-загрузка (shimmer, уже есть в pubspec) на первом фетче, понятная надпись при пустом списке, и текст ошибки, вытащенный из ApiFailure.message (или локализованный по ApiFailure.code, если хочешь более дружелюбные сообщения — заведи простой маппинг code→человеческий текст хотя бы для самых частых: WRONG_LOGIN_DATA, NOT_FOUND_*, ACCESS_DENIED, MEMBER_LIMIT_EXCEEDED, MESSAGE_TOO_LONG).
```

## Промт 8 — Финальная сверка и полировка

```
Контекст: приложение функционально собрано (промты 0–7). Открой api-docs.md раздел 10.7 (чек-лист) и пройдись по нему пункт за пунктом, вслух подтверждая каждый пункт со ссылкой на конкретный файл/строку в проекте, где это реализовано:

- [ ] Все пути заканчиваются на "/" — найди все места ручного построения путей (grep по '/chats/', '/projects/', '/profiles/' и т.д. в data/datasources) и убедись, что нет ни одного без слэша на конце.
- [ ] POST /auth/login/ уходит как form-urlencoded, не JSON.
- [ ] Ошибки везде читаются из body.error.code (кроме 429 → body.detail) — проверь, что ApiFailure/RateLimitFailure из промта 0 действительно используются во ВСЕХ фичах, а не только в auth.
- [ ] Refresh-интерцептор реально предотвращает всплытие 401 наружу в 90% случаев (протестируй вручную: дождись протухания токена за счёт короткого времени жизни 5 минут, сделай запрос, убедись что происходит silent refresh).
- [ ] has_next/total_pages для обычных списков считаются на клиенте, а не берутся из ответа сервера (перепроверь PageResult<T> реализацию).
- [ ] Аватар — POST/multipart, вложения чата — PUT/raw bytes — не перепутаны местами.
- [ ] WS обрабатывает все типы событий из 7.4 и не падает на chats.chat.deleted / двух формах ws.error.
- [ ] new_message/message_edited/message_deleted не рендерятся напрямую из WS-payload.
- [ ] resume() не отправляет больше 20 курсоров.
- [ ] avatars — 4 размера × 3 формата, нет нигде забытого plain {url}.

Дополнительно:
1. Прогони flutter analyze и dart run build_runner build --delete-conflicting-outputs, ноль ошибок.
2. Пройдись по core/error/failures.dart — убедись, что ни один catch-блок в data/repositories/*.dart не проглатывает ошибку молча (всегда либо Left(конкретный Failure), либо rethrow с логированием через Logger из core/utils).
3. Приложи ручной сценарий смок-теста (регистрация → подтверждение email опустить если не настроено письмо → логин → создание проекта → создание позиции → второй тестовый юзер откликается → первый принимает → у обоих должен появиться шанс списаться в чате, если такая связка предусмотрена продуктом, либо просто вручную создать direct-чат между двумя тестовыми пользователями → обмен сообщениями с вложением и проверкой, что WS доставляет new_message второму клиенту в реальном времени).
4. Если где-то остались куски мок-данных из исходного шаблона (Future.delayed, захардкоженные User/Message) — найди и добей (grep по "Future.delayed" и "TODO" по всему lib/features/).
```