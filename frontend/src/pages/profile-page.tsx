import { useCallback, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router';
import { useAuth } from '../features/auth/auth-context.tsx';
import {
  getProfileAvatarUrl,
  getUserInitials,
} from '../features/profile/profile-view.ts';
import {
  type ContactProvider,
  ProfileContactsEditor,
} from './profile/components/profile-contacts-editor.tsx';
import { ProfileOverviewCard } from './profile/components/profile-overview-card.tsx';
import { SessionsList } from './profile/components/sessions-list.tsx';
import {
  addProfileContact,
  createProfile,
  deleteProfileContact,
  listProfiles,
  uploadAvatar,
  updateProfile,
} from '../services/profiles/profiles.service.ts';
import { deleteSession } from '../services/sessions/sessions.service.ts';
import { listMySessions } from '../services/users/users.service.ts';
import type { ContactDTO, ProfileDTO } from '../types/api/profile.ts';
import type { SessionDTO } from '../types/api/session.ts';

type ProfileTab = 'overview' | 'edit' | 'security';

type EditFormState = {
  displayName: string;
  specialization: string;
  bio: string;
  skills: string;
  dateBirthday: string;
};

const CONTACT_PROVIDERS: ContactProvider[] = ['telegram', 'github', 'email'];

function validateContactByProvider(
  provider: ContactProvider,
  value: string,
): string | null {
  const input = value.trim();
  if (!input) return 'Введите значение контакта';

  if (provider === 'telegram') {
    if (!/^@?[a-zA-Z0-9_]{5,32}$/.test(input)) {
      return 'Telegram должен быть в формате @username (5-32 символа)';
    }
    return null;
  }

  if (provider === 'github') {
    if (!/^[a-zA-Z0-9](?:-?[a-zA-Z0-9]){0,38}$/.test(input)) {
      return 'GitHub username содержит недопустимые символы';
    }
    return null;
  }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input)) {
    return 'Email имеет неверный формат';
  }
  return null;
}

export function ProfilePage() {
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [profile, setProfile] = useState<ProfileDTO | null>(null);
  const [isLoadingProfile, setIsLoadingProfile] = useState(true);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<EditFormState>({
    displayName: '',
    specialization: '',
    bio: '',
    skills: '',
    dateBirthday: '',
  });
  const [savePending, setSavePending] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [avatarUploadPending, setAvatarUploadPending] = useState(false);
  const [sessions, setSessions] = useState<SessionDTO[]>([]);
  const [isLoadingSessions, setIsLoadingSessions] = useState(true);
  const [sessionsError, setSessionsError] = useState<string | null>(null);
  const [sessionActionPendingId, setSessionActionPendingId] = useState<
    number | null
  >(null);
  const [contactProvider, setContactProvider] =
    useState<ContactProvider>('telegram');
  const [contactValue, setContactValue] = useState('');
  const [contactPending, setContactPending] = useState(false);
  const [contactMessage, setContactMessage] = useState<string | null>(null);
  const [contactValidationError, setContactValidationError] = useState<
    string | null
  >(null);

  const activeTab: ProfileTab = (() => {
    const value = searchParams.get('tab');
    if (value === 'overview' || value === 'edit' || value === 'security') {
      return value;
    }
    return 'overview';
  })();

  const setTab = (tab: ProfileTab) => {
    setSearchParams({ tab });
  };

  const tabClass = (tab: ProfileTab) =>
    [
      'rounded-lg px-3 py-2 text-sm transition',
      activeTab === tab
        ? 'bg-zinc-100 text-zinc-900'
        : 'border border-zinc-700 text-zinc-300 hover:bg-zinc-800 hover:text-white',
    ].join(' ');

  const loadProfile = useCallback(async () => {
    if (!user?.username) return;
    setIsLoadingProfile(true);
    setProfileError(null);
    try {
      const response = await listProfiles({
        username: user.username,
        page_size: 1,
      });
      const loadedProfile = response.items?.[0] ?? null;
      setProfile(loadedProfile);
      setEditForm({
        displayName: loadedProfile?.display_name ?? '',
        specialization: loadedProfile?.specialization ?? '',
        bio: loadedProfile?.bio ?? '',
        skills: (loadedProfile?.skills ?? []).join(', '),
        dateBirthday: loadedProfile?.date_birthday ?? '',
      });
    } catch {
      setProfileError('Не удалось загрузить профиль');
    } finally {
      setIsLoadingProfile(false);
    }
  }, [user?.username]);

  const loadSessions = useCallback(async () => {
    setIsLoadingSessions(true);
    setSessionsError(null);
    try {
      const data = await listMySessions();
      setSessions(data);
    } catch {
      setSessionsError('Не удалось загрузить сессии');
    } finally {
      setIsLoadingSessions(false);
    }
  }, []);

  useEffect(() => {
    void loadProfile();
  }, [loadProfile]);

  useEffect(() => {
    void loadSessions();
  }, [loadSessions]);

  const avatarUrl = getProfileAvatarUrl(profile);
  const initials = getUserInitials(user?.username, profile?.display_name);
  const profileCompleteness = useMemo(() => {
    const filled = [
      profile?.display_name,
      profile?.specialization,
      profile?.bio,
      profile?.date_birthday,
      profile?.skills?.length ? 'skills' : '',
    ].filter(Boolean).length;
    return Math.round((filled / 5) * 100);
  }, [profile]);

  const onSaveProfile = async (event: React.FormEvent) => {
    event.preventDefault();
    setSaveMessage(null);
    setContactMessage(null);
    setSavePending(true);
    const parsedSkills = editForm.skills
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);

    try {
      if (profile?.id) {
        await updateProfile(profile.id, {
          display_name: editForm.displayName.trim() || undefined,
          specialization: editForm.specialization.trim() || undefined,
          bio: editForm.bio.trim() || undefined,
          skills: parsedSkills,
          date_birthday: editForm.dateBirthday || undefined,
        });
      } else {
        await createProfile({
          display_name: editForm.displayName.trim() || null,
          bio: editForm.bio.trim() || null,
          skills: parsedSkills,
          date_birthday: editForm.dateBirthday || null,
        });
      }
      await loadProfile();
      setSaveMessage('Профиль успешно обновлён');
    } catch {
      setSaveMessage('Не удалось сохранить профиль');
    } finally {
      setSavePending(false);
    }
  };

  const onAvatarFileChange = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    if (!event.target.files?.[0]) return;
    setSaveMessage(null);
    setAvatarUploadPending(true);
    try {
      await uploadAvatar(event.target.files[0]);
      await loadProfile();
      setSaveMessage('Аватар успешно обновлён');
    } catch {
      setSaveMessage('Не удалось загрузить аватар');
    } finally {
      setAvatarUploadPending(false);
      event.target.value = '';
    }
  };

  const onAddContact = async () => {
    if (!profile?.id) {
      setContactMessage('Сначала сохраните профиль');
      return;
    }
    const validationError = validateContactByProvider(
      contactProvider,
      contactValue,
    );
    if (validationError) {
      setContactValidationError(validationError);
      return;
    }

    setContactValidationError(null);
    setContactPending(true);
    setContactMessage(null);
    const optimisticContact: ContactDTO = {
      profile_id: profile.id,
      provider: contactProvider,
      contact: contactValue.trim(),
    };
    const previousContacts = profile.contacts;
    setProfile((prev) =>
      prev
        ? {
            ...prev,
            contacts: [...prev.contacts, optimisticContact],
          }
        : prev,
    );

    try {
      await addProfileContact(profile.id, {
        provider: contactProvider,
        contact: contactValue.trim(),
      });
      setContactValue('');
      setContactMessage('Контакт добавлен');
    } catch {
      setProfile((prev) =>
        prev
          ? {
              ...prev,
              contacts: previousContacts,
            }
          : prev,
      );
      setContactMessage('Не удалось добавить контакт');
    } finally {
      setContactPending(false);
    }
  };

  const onDeleteContact = async (provider: string) => {
    if (!profile?.id) return;
    setContactPending(true);
    setContactMessage(null);
    const previousContacts = profile.contacts;
    const optimisticContacts = profile.contacts.filter(
      (contact) => contact.provider !== provider,
    );
    setProfile((prev) =>
      prev
        ? {
            ...prev,
            contacts: optimisticContacts,
          }
        : prev,
    );
    try {
      await deleteProfileContact(profile.id, provider);
      setContactMessage('Контакт удалён');
    } catch {
      setProfile((prev) =>
        prev
          ? {
              ...prev,
              contacts: previousContacts,
            }
          : prev,
      );
      setContactMessage('Не удалось удалить контакт');
    } finally {
      setContactPending(false);
    }
  };

  const onTerminateSession = async (sessionId: number) => {
    setSessionActionPendingId(sessionId);
    setSessionsError(null);
    const previousSessions = sessions;
    setSessions((prev) =>
      prev.map((session) =>
        session.id === sessionId ? { ...session, is_active: false } : session,
      ),
    );
    try {
      await deleteSession(sessionId);
    } catch {
      setSessions(previousSessions);
      setSessionsError('Не удалось завершить сессию');
    } finally {
      setSessionActionPendingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-6">
        <h1 className="text-2xl font-semibold">Личный кабинет</h1>
        <p className="mt-2 text-sm text-zinc-400">
          Управляйте профилем, контактами, аватаром и безопасностью аккаунта.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setTab('overview')}
            className={tabClass('overview')}
          >
            Обзор
          </button>
          <button
            type="button"
            onClick={() => setTab('edit')}
            className={tabClass('edit')}
          >
            Редактирование
          </button>
          <button
            type="button"
            onClick={() => setTab('security')}
            className={tabClass('security')}
          >
            Безопасность
          </button>
        </div>
      </section>

      {activeTab === 'overview' ? (
        <section className="grid gap-4 md:grid-cols-2">
          <article className="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-6">
            <h2 className="text-lg font-medium">Профиль пользователя</h2>
            <ProfileOverviewCard
              isLoading={isLoadingProfile}
              error={profileError}
              avatarUrl={avatarUrl}
              initials={initials}
              displayName={
                profile?.display_name || user?.username || 'Пользователь'
              }
              email={user?.email ?? ''}
              userId={user?.id ?? null}
              username={user?.username ?? '—'}
              specialization={profile?.specialization || 'Не указано'}
              dateBirthday={profile?.date_birthday || 'Не указана'}
            />
          </article>

          <article className="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-6">
            <h2 className="text-lg font-medium">Заполненность профиля</h2>
            <p className="mt-4 text-sm text-zinc-300">
              Заполнено:{' '}
              <span className="font-semibold">{profileCompleteness}%</span>
            </p>
            <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-zinc-800">
              <div
                className="h-full rounded-full bg-zinc-100 transition-all"
                style={{ width: `${profileCompleteness}%` }}
              />
            </div>
            <p className="mt-4 text-xs text-zinc-500">
              Добавьте специализацию, bio и контакты для лучшей видимости в
              системе.
            </p>
          </article>
        </section>
      ) : null}

      {activeTab === 'edit' ? (
        <section className="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-6">
          <h2 className="text-lg font-medium">Редактирование профиля</h2>
          <p className="mt-2 text-sm text-zinc-500">
            Изменения применяются к вашему публичному профилю.
          </p>

          <form
            className="mt-6 grid gap-4 md:grid-cols-2"
            onSubmit={onSaveProfile}
          >
            <div className="md:col-span-2 flex items-center gap-4">
              {avatarUrl ? (
                <img
                  src={avatarUrl}
                  alt="Текущий аватар"
                  className="h-16 w-16 rounded-full border border-zinc-700 object-cover"
                />
              ) : (
                <div className="flex h-16 w-16 items-center justify-center rounded-full border border-zinc-700 bg-zinc-800 text-lg font-semibold">
                  {initials}
                </div>
              )}
              <label className="cursor-pointer rounded-lg border border-zinc-700 px-3 py-2 text-sm text-zinc-200 hover:bg-zinc-800">
                {avatarUploadPending
                  ? 'Загрузка...'
                  : 'Загрузить / сменить аватар'}
                <input
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={(event) => void onAvatarFileChange(event)}
                  disabled={avatarUploadPending}
                />
              </label>
            </div>

            <label className="text-sm text-zinc-300">
              Display name
              <input
                value={editForm.displayName}
                onChange={(event) =>
                  setEditForm((prev) => ({
                    ...prev,
                    displayName: event.target.value,
                  }))
                }
                className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100 outline-none focus:border-zinc-500"
              />
            </label>

            <label className="text-sm text-zinc-300">
              Специализация
              <input
                value={editForm.specialization}
                onChange={(event) =>
                  setEditForm((prev) => ({
                    ...prev,
                    specialization: event.target.value,
                  }))
                }
                className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100 outline-none focus:border-zinc-500"
              />
            </label>

            <label className="text-sm text-zinc-300">
              Дата рождения
              <input
                type="date"
                value={editForm.dateBirthday}
                onChange={(event) =>
                  setEditForm((prev) => ({
                    ...prev,
                    dateBirthday: event.target.value,
                  }))
                }
                className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100 outline-none focus:border-zinc-500"
              />
            </label>

            <label className="text-sm text-zinc-300">
              Навыки (через запятую)
              <input
                value={editForm.skills}
                onChange={(event) =>
                  setEditForm((prev) => ({
                    ...prev,
                    skills: event.target.value,
                  }))
                }
                className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100 outline-none focus:border-zinc-500"
              />
            </label>

            <label className="text-sm text-zinc-300 md:col-span-2">
              О себе
              <textarea
                rows={4}
                value={editForm.bio}
                onChange={(event) =>
                  setEditForm((prev) => ({ ...prev, bio: event.target.value }))
                }
                className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100 outline-none focus:border-zinc-500"
              />
            </label>

            <ProfileContactsEditor
              providers={CONTACT_PROVIDERS}
              provider={contactProvider}
              value={contactValue}
              contacts={profile?.contacts ?? []}
              isPending={contactPending}
              message={contactMessage}
              validationError={contactValidationError}
              onProviderChange={setContactProvider}
              onValueChange={setContactValue}
              onAdd={() => void onAddContact()}
              onDelete={(provider) => void onDeleteContact(provider)}
            />

            <div className="md:col-span-2 flex items-center gap-3">
              <button
                type="submit"
                disabled={savePending}
                className="rounded-lg bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-900 hover:bg-white disabled:opacity-50"
              >
                {savePending ? 'Сохранение...' : 'Сохранить профиль'}
              </button>
              {saveMessage ? (
                <span className="text-sm text-zinc-400">{saveMessage}</span>
              ) : null}
            </div>
          </form>
        </section>
      ) : null}

      {activeTab === 'security' ? (
        <section className="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-6">
          <h2 className="text-lg font-medium">Безопасность и сессии</h2>
          <SessionsList
            isLoading={isLoadingSessions}
            error={sessionsError}
            sessions={sessions}
            pendingId={sessionActionPendingId}
            onTerminate={(sessionId) => void onTerminateSession(sessionId)}
          />
        </section>
      ) : null}
    </div>
  );
}
