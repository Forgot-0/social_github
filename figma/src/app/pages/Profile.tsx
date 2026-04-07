import { useEffect, useMemo, useRef, useState } from 'react';
import { User, Mail, Calendar, MapPin, Briefcase, Edit, Plus, X, Upload, Camera } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../lib/api';
import { toast } from 'sonner';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';

interface ProfileData {
  id?: number;
  user_id?: number;
  display_name: string;
  bio: string;
  specialization: string;
  skills: string[];
  date_birthday?: string;
  contacts?: Array<{ provider: string; contact: string }>;
  avatars?: Record<string, { url?: string } | string>;
}

const emptyProfile = (username = ''): ProfileData => ({
  display_name: username,
  bio: '',
  specialization: '',
  skills: [],
  date_birthday: '',
  contacts: [],
  avatars: {},
});

function getAvatarUrl(profile?: ProfileData | null) {
  const avatars = profile?.avatars;
  if (!avatars || typeof avatars !== 'object') return '';
  const preferred = avatars['256'] || avatars['128'] || avatars.medium || avatars.large || avatars.small;
  if (typeof preferred === 'string') return preferred;
  if (preferred && typeof preferred === 'object' && 'url' in preferred) return String((preferred as any).url);
  const firstValue = Object.values(avatars)[0];
  if (typeof firstValue === 'string') return firstValue;
  if (firstValue && typeof firstValue === 'object' && 'url' in (firstValue as any)) return String((firstValue as any).url);
  return '';
}

function getInitial(value?: string) {
  return value?.trim()?.[0]?.toUpperCase() || 'И';
}

export function Profile() {
  const { user } = useAuth();
  const { id } = useParams();
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editedProfile, setEditedProfile] = useState<ProfileData>(emptyProfile());
  const [newSkill, setNewSkill] = useState('');
  const [loading, setLoading] = useState(true);
  const [projects, setProjects] = useState<any[]>([]);
  const [avatarUploading, setAvatarUploading] = useState(false);
  const avatarInputRef = useRef<HTMLInputElement | null>(null);

  const requestedProfileId = useMemo(() => {
    if (id) {
      const numeric = Number(id);
      return Number.isFinite(numeric) ? numeric : null;
    }
    return user?.id ?? null;
  }, [id, user?.id]);

  const isOwnProfile = Boolean(user && requestedProfileId && user.id === requestedProfileId);

  useEffect(() => {
    void loadProfile();
  }, [requestedProfileId, user?.id]);

  useEffect(() => {
    if (!isOwnProfile || !user) {
      setProjects([]);
      return;
    }
    void loadProjects();
  }, [isOwnProfile, user?.id]);

  const loadProfile = async () => {
    if (!requestedProfileId) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      let profileData: any = null;

      try {
        profileData = await api.getProfile(requestedProfileId);
      } catch (error: any) {
        if (!(isOwnProfile && error?.error?.code === 'NOT_FOUND_PROFILE')) {
          throw error;
        }
      }

      if (profileData) {
        const normalized = {
          ...emptyProfile(isOwnProfile ? user?.username || '' : ''),
          ...profileData,
          skills: Array.isArray(profileData?.skills) ? profileData.skills : [],
          contacts: Array.isArray(profileData?.contacts) ? profileData.contacts : [],
          avatars: profileData?.avatars || {},
        };
        setProfile(normalized);
        setEditedProfile(normalized);
      } else if (isOwnProfile) {
        const fallback = emptyProfile(user?.username || '');
        setProfile(null);
        setEditedProfile(fallback);
      } else {
        setProfile(null);
      }
    } catch (error: any) {
      console.error('Failed to load profile:', error);
      toast.error(error?.error?.message || 'Не удалось загрузить профиль');
      if (isOwnProfile) {
        const fallback = emptyProfile(user?.username || '');
        setProfile(null);
        setEditedProfile(fallback);
      } else {
        setProfile(null);
      }
    } finally {
      setLoading(false);
    }
  };

  const loadProjects = async () => {
    try {
      const data = await api.getMyProjects({ page: 1, page_size: 8 });
      const items = Array.isArray(data?.items) ? data.items : Array.isArray(data) ? data : [];
      setProjects(items);
    } catch (error: any) {
      console.error('Failed to load projects:', error);
      setProjects([]);
    }
  };

  const handleSave = async () => {
    if (!user) return;

    try {
      const createPayload = {
        display_name: editedProfile.display_name,
        bio: editedProfile.bio,
        skills: editedProfile.skills,
        date_birthday: editedProfile.date_birthday || undefined,
      };

      const updatePayload = {
        ...createPayload,
        specialization: editedProfile.specialization,
      };

      if (profile?.id) {
        await api.updateProfile(user.id, updatePayload);
        toast.success('Профиль обновлен');
      } else {
        await api.createProfile(createPayload);
        toast.success('Профиль создан');
      }
      await loadProfile();
      window.dispatchEvent(new Event('profile-updated'));
      setIsEditing(false);
    } catch (error: any) {
      console.error('Failed to save profile:', error);
      toast.error(error?.error?.message || 'Ошибка сохранения профиля');
    }
  };

  const handleCancel = () => {
    setEditedProfile(profile || emptyProfile(user?.username || ''));
    setIsEditing(false);
  };

  const addSkill = () => {
    const skill = newSkill.trim();
    if (skill && !editedProfile.skills.includes(skill)) {
      setEditedProfile({
        ...editedProfile,
        skills: [...editedProfile.skills, skill],
      });
      setNewSkill('');
    }
  };

  const removeSkill = (skill: string) => {
    setEditedProfile({
      ...editedProfile,
      skills: editedProfile.skills.filter((s) => s !== skill),
    });
  };

  const handleAvatarUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !user || !isOwnProfile) return;

    if (!file.type.startsWith('image/')) {
      toast.error('Можно загрузить только изображение');
      event.target.value = '';
      return;
    }

    try {
      setAvatarUploading(true);

      if (!profile?.id) {
        await api.createProfile({
          display_name: editedProfile.display_name || user.username,
          bio: editedProfile.bio,
          skills: editedProfile.skills,
          date_birthday: editedProfile.date_birthday || undefined,
        });
        await loadProfile();
      }

      await api.uploadAvatar(file);
      toast.success('Аватар обновлен');
      await loadProfile();
      window.dispatchEvent(new Event('profile-updated'));
    } catch (error: any) {
      console.error('Failed to upload avatar:', error);
      toast.error(error?.error?.message || 'Не удалось загрузить аватар');
    } finally {
      setAvatarUploading(false);
      event.target.value = '';
    }
  };

  if (loading) {
    return (
      <div className="py-20 text-center">
        <div className="inline-block h-12 w-12 animate-spin rounded-full border-b-2 border-primary"></div>
        <p className="mt-4 text-muted-foreground">Загрузка профиля...</p>
      </div>
    );
  }

  if (!requestedProfileId) {
    return (
      <div className="py-20 text-center">
        <h2 className="mb-4 text-2xl font-bold">Войдите, чтобы увидеть профиль</h2>
      </div>
    );
  }

  if (!profile && !isOwnProfile) {
    return (
      <div className="py-20 text-center">
        <h2 className="mb-4 text-2xl font-bold">Профиль не найден</h2>
        <p className="text-muted-foreground">Проверьте ссылку на профиль пользователя.</p>
      </div>
    );
  }

  const displayProfile = profile || editedProfile;
  const avatarUrl = getAvatarUrl(displayProfile);
  const displayName = displayProfile.display_name || (isOwnProfile ? user?.username : `Пользователь #${requestedProfileId}`) || 'Профиль';

  return (
    <div className="py-12">
      <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="mb-4 text-3xl font-bold text-foreground md:text-4xl">{isOwnProfile ? 'Профиль' : 'Профиль участника'}</h1>
          <p className="text-lg text-muted-foreground">
            {isOwnProfile ? 'Управляйте своей информацией и настройками' : 'Просмотр публичной информации участника проекта'}
          </p>
        </div>

        <div className="mb-6 overflow-hidden rounded-xl border border-border bg-white shadow-sm">
          <div className="bg-gradient-to-r from-primary to-accent p-8">
            <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
              <div className="flex items-center gap-4">
                <div className="relative">
                  <Avatar className="h-24 w-24 ring-4 ring-white/40 shadow-lg">
                    <AvatarImage src={avatarUrl} alt={displayName} className="object-cover" />
                    <AvatarFallback className="bg-white text-3xl font-bold text-primary">
                      {getInitial(displayName)}
                    </AvatarFallback>
                  </Avatar>
                  {isOwnProfile ? (
                    <>
                      <button
                        type="button"
                        onClick={() => avatarInputRef.current?.click()}
                        disabled={avatarUploading}
                        className="absolute -bottom-1 -right-1 inline-flex h-10 w-10 items-center justify-center rounded-full bg-white text-primary shadow-md transition-colors hover:bg-secondary disabled:cursor-not-allowed disabled:opacity-70"
                        aria-label="Загрузить аватар"
                      >
                        {avatarUploading ? <Upload className="h-4 w-4 animate-pulse" /> : <Camera className="h-4 w-4" />}
                      </button>
                      <input ref={avatarInputRef} type="file" accept="image/*" className="hidden" onChange={handleAvatarUpload} />
                    </>
                  ) : null}
                </div>
                <div className="text-white">
                  <h2 className="mb-1 text-2xl font-bold">{displayName}</h2>
                  {isOwnProfile && user ? <p className="opacity-90">@{user.username}</p> : <p className="opacity-90">ID профиля: {requestedProfileId}</p>}
                </div>
              </div>
              {isOwnProfile && !isEditing ? (
                <button
                  onClick={() => setIsEditing(true)}
                  className="inline-flex items-center gap-2 self-start rounded-xl bg-white px-4 py-2 text-primary transition-colors hover:bg-gray-100"
                >
                  <Edit className="h-4 w-4" />
                  <span>Редактировать</span>
                </button>
              ) : null}
            </div>
          </div>

          <div className="p-8">
            {isOwnProfile && isEditing ? (
              <div className="space-y-6">
                <div>
                  <label className="mb-2 block text-sm">Отображаемое имя</label>
                  <input
                    type="text"
                    value={editedProfile.display_name}
                    onChange={(e) => setEditedProfile({ ...editedProfile, display_name: e.target.value })}
                    className="app-input"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-sm">Специализация</label>
                  <input
                    type="text"
                    value={editedProfile.specialization}
                    onChange={(e) => setEditedProfile({ ...editedProfile, specialization: e.target.value })}
                    className="app-input"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-sm">Дата рождения</label>
                  <input
                    type="date"
                    value={editedProfile.date_birthday || ''}
                    onChange={(e) => setEditedProfile({ ...editedProfile, date_birthday: e.target.value })}
                    className="app-input"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-sm">О себе</label>
                  <textarea
                    value={editedProfile.bio}
                    onChange={(e) => setEditedProfile({ ...editedProfile, bio: e.target.value })}
                    rows={4}
                    className="app-textarea"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-sm">Навыки</label>
                  <div className="mb-3 flex gap-2">
                    <input
                      type="text"
                      value={newSkill}
                      onChange={(e) => setNewSkill(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          addSkill();
                        }
                      }}
                      placeholder="Добавить навык..."
                      className="app-input flex-1"
                    />
                    <button type="button" onClick={addSkill} className="rounded-xl bg-primary px-4 py-3 text-white transition-colors hover:bg-accent">
                      <Plus className="h-5 w-5" />
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {editedProfile.skills.map((skill) => (
                      <span key={skill} className="flex items-center gap-2 rounded-full bg-secondary px-3 py-1 text-secondary-foreground">
                        <span>{skill}</span>
                        <button type="button" onClick={() => removeSkill(skill)} className="hover:text-destructive">
                          <X className="h-3 w-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                </div>
                <div className="flex gap-3 pt-4">
                  <button onClick={handleSave} className="rounded-xl bg-primary px-6 py-3 text-white transition-colors hover:bg-accent">
                    Сохранить
                  </button>
                  <button onClick={handleCancel} className="rounded-xl border border-border px-6 py-3 text-foreground transition-colors hover:bg-secondary">
                    Отмена
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                <div>
                  <div className="mb-2 flex items-center gap-2 text-muted-foreground">
                    <Briefcase className="h-4 w-4" />
                    <span className="text-sm">Специализация</span>
                  </div>
                  <p className="text-lg">{displayProfile.specialization || 'Не указана'}</p>
                </div>
                <div>
                  <div className="mb-2 flex items-center gap-2 text-muted-foreground">
                    <User className="h-4 w-4" />
                    <span className="text-sm">О себе</span>
                  </div>
                  <p className="leading-relaxed text-muted-foreground">{displayProfile.bio || 'Нет информации'}</p>
                </div>
                {isOwnProfile && user ? (
                  <div>
                    <div className="mb-3 flex items-center gap-2 text-muted-foreground">
                      <Mail className="h-4 w-4" />
                      <span className="text-sm">Email</span>
                    </div>
                    <p>{user.email}</p>
                  </div>
                ) : null}
                {displayProfile.date_birthday ? (
                  <div>
                    <div className="mb-3 flex items-center gap-2 text-muted-foreground">
                      <Calendar className="h-4 w-4" />
                      <span className="text-sm">Дата рождения</span>
                    </div>
                    <p>{new Date(displayProfile.date_birthday).toLocaleDateString('ru-RU')}</p>
                  </div>
                ) : null}
              </div>
            )}
          </div>
        </div>

        {!isEditing && displayProfile.skills && displayProfile.skills.length > 0 ? (
          <div className="mb-6 rounded-xl border border-border bg-white p-8 shadow-sm">
            <h3 className="mb-4 text-xl font-semibold">Навыки</h3>
            <div className="flex flex-wrap gap-2">
              {displayProfile.skills.map((skill: string) => (
                <span key={skill} className="rounded-full bg-primary/10 px-4 py-2 text-primary">
                  {skill}
                </span>
              ))}
            </div>
          </div>
        ) : null}

        {isOwnProfile && !isEditing && projects.length > 0 ? (
          <div className="mb-6 overflow-hidden rounded-3xl border border-border bg-white shadow-sm">
            <div className="flex flex-col gap-3 border-b border-border bg-gradient-to-r from-primary/6 via-white to-accent/8 px-8 py-6 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h3 className="text-xl font-semibold">Мои проекты</h3>
                <p className="mt-1 text-sm text-muted-foreground">Коллекция ваших активных проектов в стиле сайта</p>
              </div>
              <Link to="/my-projects" className="inline-flex items-center justify-center rounded-xl border border-primary/20 bg-white px-4 py-2 text-sm font-medium text-primary transition-colors hover:bg-secondary">
                Открыть все проекты
              </Link>
            </div>
            <div className="grid gap-4 p-6 md:grid-cols-2">
              {projects.slice(0, 4).map((project: any) => (
                <Link
                  key={project.id}
                  to={`/projects/${project.id}`}
                  className="group rounded-2xl border border-border bg-gradient-to-br from-white via-white to-secondary/35 p-5 transition-all hover:-translate-y-0.5 hover:border-primary/20 hover:shadow-md"
                >
                  <div className="mb-3 flex items-start justify-between gap-3">
                    <div>
                      <h4 className="text-lg font-semibold transition-colors group-hover:text-primary">{project.name}</h4>
                      <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">{project.small_description}</p>
                    </div>
                    <span className="rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary">Проект</span>
                  </div>
                  {Array.isArray(project.tags) && project.tags.length > 0 ? (
                    <div className="mb-4 flex flex-wrap gap-2">
                      {project.tags.slice(0, 3).map((tag: string) => (
                        <span key={tag} className="rounded-full bg-secondary px-3 py-1 text-xs text-secondary-foreground">
                          {tag}
                        </span>
                      ))}
                    </div>
                  ) : null}
                  <div className="text-sm font-medium text-primary">Перейти к проекту →</div>
                </Link>
              ))}
            </div>
          </div>
        ) : null}

        {!isEditing && displayProfile.contacts && displayProfile.contacts.length > 0 ? (
          <div className="rounded-xl border border-border bg-white p-8 shadow-sm">
            <h3 className="mb-4 text-xl font-semibold">Контакты</h3>
            <div className="space-y-3">
              {displayProfile.contacts.map((contact: any, index: number) => (
                <div key={index} className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
                    <MapPin className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <div className="text-sm capitalize text-muted-foreground">{contact.provider}</div>
                    <div>{contact.contact}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
