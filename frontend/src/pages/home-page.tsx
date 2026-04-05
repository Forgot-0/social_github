import { appEnv } from '../app/env';

const architectureProblems = [
  'Отсутствовала маршрутизация и базовый каркас приложения.',
  'Не было точки для централизованной инициализации API-слоя.',
  'Конфигурация окружения не валидировалась и не документировалась в коде.',
  'Пустой UI затруднял тестирование и развитие frontend-модулей.',
];

const improvements = [
  'Добавлен App Shell с понятной структурой разделов и стартовой страницей.',
  'Добавлен ApiProvider (dependency injection через React Context).',
  'Добавлен единый env-модуль с нормализацией API base URL.',
  'Собрана страница технического аудита с видимыми следующими шагами.',
];

export const HomePage = () => {
  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col gap-8 px-6 py-10">
      <header className="space-y-3">
        <h1 className="text-3xl font-semibold tracking-tight">
          {appEnv.appName}
        </h1>
        <p className="text-slate-300">
          Технический аудит frontend и первичное оздоровление архитектуры.
        </p>
      </header>

      <section className="rounded-2xl border border-slate-700 bg-slate-900/70 p-6">
        <h2 className="mb-3 text-xl font-medium">Найденные проблемы</h2>
        <ul className="list-disc space-y-2 pl-6 text-slate-300">
          {architectureProblems.map((problem) => (
            <li key={problem}>{problem}</li>
          ))}
        </ul>
      </section>

      <section className="rounded-2xl border border-emerald-900 bg-emerald-950/40 p-6">
        <h2 className="mb-3 text-xl font-medium text-emerald-300">
          Что уже улучшено
        </h2>
        <ul className="list-disc space-y-2 pl-6 text-emerald-200">
          {improvements.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section className="rounded-2xl border border-slate-700 bg-slate-900/70 p-6">
        <h2 className="mb-3 text-xl font-medium">
          Следующие архитектурные шаги
        </h2>
        <ol className="list-decimal space-y-2 pl-6 text-slate-300">
          <li>Вынести каждый бизнес-модуль в отдельный feature package.</li>
          <li>
            Добавить state-layer (RTK Query/Zustand) с кэшированием запросов.
          </li>
          <li>Внедрить error boundary + telemetry (Sentry/OpenTelemetry).</li>
          <li>Покрыть критичный UI Playwright и Vitest тестами.</li>
        </ol>
      </section>
    </main>
  );
};
