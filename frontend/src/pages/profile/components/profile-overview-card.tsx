import { TagChips } from '../../../components/tag_chips';

type ProfileOverviewCardProps = {
  isLoading: boolean;
  error: string | null;
  avatarUrl: string | null;
  initials: string;
  displayName: string;
  email: string;
  userId: number | null;
  username: string;
  specialization: string;
  dateBirthday: string;
  skills?: string[];
};

export function ProfileOverviewCard({
  isLoading,
  error,
  avatarUrl,
  initials,
  displayName,
  email,
  userId,
  username,
  specialization,
  dateBirthday,
  skills = [],
}: ProfileOverviewCardProps) {
  if (isLoading) {
    return <p className="mt-4 text-sm text-zinc-500">Загрузка профиля...</p>;
  }

  if (error) {
    return <p className="mt-4 text-sm text-red-300">{error}</p>;
  }

  return (
    <div className="mt-4 space-y-4 text-sm text-zinc-300">
      <div className="flex items-center gap-3">
        {avatarUrl ? (
          <img
            src={avatarUrl}
            alt="Аватар пользователя"
            className="h-12 w-12 rounded-full border border-zinc-700 object-cover"
          />
        ) : (
          <div className="flex h-12 w-12 items-center justify-center rounded-full border border-zinc-700 bg-zinc-800 text-sm font-semibold">
            {initials}
          </div>
        )}
        <div>
          <p className="font-medium text-zinc-100">{displayName}</p>
          <p className="text-xs text-zinc-500">{email}</p>
        </div>
      </div>

      <ul className="space-y-2">
        <li>
          <span className="text-zinc-500">ID:</span> {userId ?? '—'}
        </li>
        <li>
          <span className="text-zinc-500">Логин:</span> {username}
        </li>
        <li>
          <span className="text-zinc-500">Специализация:</span> {specialization}
        </li>
        <li>
          <span className="text-zinc-500">Дата рождения:</span> {dateBirthday}
        </li>
      </ul>
      <div>
        <p className="mb-2 text-xs uppercase tracking-wide text-zinc-500">
          Навыки
        </p>
        <TagChips items={skills} emptyText="Навыки не указаны" />
      </div>
    </div>
  );
}
