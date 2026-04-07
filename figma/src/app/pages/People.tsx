import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, Sparkles, UsersRound, X } from 'lucide-react';
import { api } from '../lib/api';
import { toast } from 'sonner';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { TagSearchFilter, normalizeFilterValue } from '../components/TagSearchFilter';

interface ProfileRecord {
  id: number;
  display_name?: string;
  specialization?: string;
  bio?: string;
  skills?: string[];
  contacts?: Array<{ provider: string; contact: string }>;
  avatars?: Record<string, { url?: string } | string>;
  username?: string;
  __sources?: string[];
}

function getAvatarUrl(profile?: ProfileRecord | null) {
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

function mergeProfilesWithSource(list: Array<{ response: any; source: string }>) {
  const map = new Map<number, ProfileRecord>();

  list.forEach(({ response, source }) => {
    const items = Array.isArray(response?.items) ? response.items : Array.isArray(response) ? response : [];
    items.forEach((item: any) => {
      if (typeof item?.id !== 'number') return;
      const existing = map.get(item.id);
      if (existing) {
        const nextSources = new Set([...(existing.__sources || []), source]);
        map.set(item.id, { ...existing, ...item, __sources: Array.from(nextSources) });
      } else {
        map.set(item.id, { ...item, __sources: [source] });
      }
    });
  });

  return Array.from(map.values());
}

function scoreProfile(profile: ProfileRecord, query: string) {
  const q = normalizeFilterValue(query);
  if (!q) return 0;

  const displayName = normalizeFilterValue(profile.display_name || '');
  const username = normalizeFilterValue(profile.username || '');
  const specialization = normalizeFilterValue(profile.specialization || '');
  const bio = normalizeFilterValue(profile.bio || '');
  const skills = Array.isArray(profile.skills) ? profile.skills.map((skill) => normalizeFilterValue(skill)) : [];
  const sources = new Set(profile.__sources || []);

  let score = 0;
  if (displayName.startsWith(q)) score += 180;
  else if (displayName.includes(q)) score += 130;
  if (sources.has('display_name')) score += 55;

  if (username.startsWith(q)) score += 110;
  else if (username.includes(q)) score += 80;
  if (sources.has('username')) score += 30;

  if (specialization.startsWith(q)) score += 45;
  else if (specialization.includes(q)) score += 28;
  if (bio.includes(q)) score += 12;

  skills.forEach((skill) => {
    if (skill === q) score += 55;
    else if (skill.includes(q)) score += 18;
  });

  return score;
}

function matchesTags(profile: ProfileRecord, selectedTags: string[]) {
  if (selectedTags.length === 0) return true;
  const skills = Array.isArray(profile.skills) ? profile.skills.map((skill) => normalizeFilterValue(skill)) : [];
  return selectedTags.every((tag) => skills.some((skill) => skill.includes(normalizeFilterValue(tag))));
}

function highlightText(text: string, query: string) {
  if (!query.trim()) return text;
  const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const regex = new RegExp(`(${escaped})`, 'ig');
  const parts = text.split(regex);
  return parts.map((part, index) =>
    index % 2 === 1 ? (
      <mark key={`${part}-${index}`} className="rounded bg-primary/12 px-0.5 text-primary">
        {part}
      </mark>
    ) : (
      <span key={`${part}-${index}`}>{part}</span>
    )
  );
}

function getSearchBadges(profile: ProfileRecord, query: string) {
  const badges: string[] = [];
  const q = normalizeFilterValue(query);
  if (!q) return badges;

  if (normalizeFilterValue(profile.display_name || '').includes(q)) badges.push('никнейм');
  if ((profile.__sources || []).includes('username')) badges.push('username');
  const skill = Array.isArray(profile.skills)
    ? profile.skills.find((item) => normalizeFilterValue(item).includes(q))
    : null;
  if (skill) badges.push(`тег: ${skill}`);

  return badges.slice(0, 3);
}

export function People() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [profiles, setProfiles] = useState<ProfileRecord[]>([]);
  const [suggestions, setSuggestions] = useState<ProfileRecord[]>([]);
  const [activeProfileId, setActiveProfileId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const timeoutId = window.setTimeout(async () => {
      const query = searchQuery.trim();
      if (!query) {
        setSuggestions([]);
        return;
      }

      try {
        setSuggestionsLoading(true);
        const [byDisplayName, byUsername] = await Promise.all([
          api.getProfiles({ display_name: query, page: 1, page_size: 6, sort: 'display_name:asc' }),
          api.getProfiles({ username: query, page: 1, page_size: 6, sort: 'display_name:asc' }),
        ]);
        if (cancelled) return;

        const merged = mergeProfilesWithSource([
          { response: byDisplayName, source: 'display_name' },
          { response: byUsername, source: 'username' },
        ])
          .filter((profile) => matchesTags(profile, selectedTags))
          .sort((left, right) => {
            const scoreDiff = scoreProfile(right, query) - scoreProfile(left, query);
            if (scoreDiff !== 0) return scoreDiff;
            return String(left.display_name || '').localeCompare(String(right.display_name || ''), 'ru');
          })
          .slice(0, 6);

        setSuggestions(merged);
      } catch (error: any) {
        if (!cancelled) {
          console.error('Failed to load profile suggestions:', error);
          setSuggestions([]);
        }
      } finally {
        if (!cancelled) setSuggestionsLoading(false);
      }
    }, 220);

    return () => {
      cancelled = true;
      window.clearTimeout(timeoutId);
    };
  }, [searchQuery, selectedTags]);

  useEffect(() => {
    let cancelled = false;
    const timeoutId = window.setTimeout(async () => {
      try {
        setLoading(true);
        const query = searchQuery.trim();

        if (activeProfileId && query) {
          const exact = await api.getProfile(activeProfileId);
          if (cancelled) return;
          const normalized = exact ? [{ ...exact, __sources: ['selected'] }] : [];
          setProfiles(normalized.filter((profile) => matchesTags(profile, selectedTags)));
          return;
        }

        if (!query) {
          const response = await api.getProfiles({ page: 1, page_size: 24, sort: 'display_name:asc' });
          if (cancelled) return;
          const items = Array.isArray(response?.items) ? response.items : Array.isArray(response) ? response : [];
          const filtered = items.filter((profile: ProfileRecord) => matchesTags(profile, selectedTags));
          setProfiles(filtered);
          return;
        }

        const [byDisplayName, byUsername] = await Promise.all([
          api.getProfiles({ display_name: query, page: 1, page_size: 24, sort: 'display_name:asc' }),
          api.getProfiles({ username: query, page: 1, page_size: 24, sort: 'display_name:asc' }),
        ]);
        if (cancelled) return;

        const merged = mergeProfilesWithSource([
          { response: byDisplayName, source: 'display_name' },
          { response: byUsername, source: 'username' },
        ])
          .filter((profile) => matchesTags(profile, selectedTags))
          .sort((left, right) => {
            const scoreDiff = scoreProfile(right, query) - scoreProfile(left, query);
            if (scoreDiff !== 0) return scoreDiff;
            return String(left.display_name || '').localeCompare(String(right.display_name || ''), 'ru');
          });

        setProfiles(merged);
      } catch (error: any) {
        if (!cancelled) {
          console.error('Failed to load people:', error);
          toast.error(error?.error?.message || 'Не удалось загрузить людей');
          setProfiles([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }, 260);

    return () => {
      cancelled = true;
      window.clearTimeout(timeoutId);
    };
  }, [searchQuery, selectedTags, activeProfileId]);

  const availableTags = useMemo(
    () => Array.from(new Set(profiles.flatMap((profile) => profile.skills || []))).sort((a, b) => a.localeCompare(b, 'ru')),
    [profiles],
  );

  const hasFilters = searchQuery.trim().length > 0 || selectedTags.length > 0 || activeProfileId !== null;

  return (
    <div className="py-12">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="mb-4 text-3xl font-bold text-foreground md:text-4xl">Люди</h1>
          <p className="max-w-3xl text-lg text-muted-foreground">
            Ищите участников сообщества по никнейму, username и тегам профиля. Поиск в выпадающем списке сначала показывает совпадения по никнейму, а затем по username.
          </p>
        </div>

        <div className="mb-8 space-y-4">
          <div className="rounded-3xl border border-border bg-white p-5 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <label className="mb-3 block text-sm font-semibold text-foreground">Поиск по людям</label>
                <p className="text-sm text-muted-foreground">Одна строка ищет и по никнейму, и по username. Приоритет — совпадения по никнейму.</p>
              </div>
              {hasFilters ? (
                <button
                  type="button"
                  onClick={() => {
                    setSearchQuery('');
                    setSelectedTags([]);
                    setActiveProfileId(null);
                    setSuggestions([]);
                  }}
                  className="text-sm font-medium text-primary hover:underline"
                >
                  Сбросить фильтры
                </button>
              ) : null}
            </div>

            <div className="relative mt-4">
              <Search className="absolute left-3 top-3.5 h-5 w-5 text-muted-foreground" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setActiveProfileId(null);
                }}
                placeholder="Например: Анна, anna_dev, backend"
                className="app-input w-full pl-10 pr-11"
              />
              {searchQuery ? (
                <button
                  type="button"
                  onClick={() => {
                    setSearchQuery('');
                    setActiveProfileId(null);
                    setSuggestions([]);
                  }}
                  className="absolute right-3 top-3 inline-flex h-6 w-6 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                  aria-label="Очистить поиск"
                >
                  <X className="h-4 w-4" />
                </button>
              ) : null}

              {searchQuery.trim() ? (
                <div className="absolute left-0 right-0 top-[calc(100%+10px)] z-20 rounded-3xl border border-border bg-white p-3 shadow-2xl shadow-slate-900/10">
                  <div className="mb-2 flex items-center justify-between px-1 text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
                    <span>Подсказки</span>
                    {suggestionsLoading ? <span>Ищем…</span> : null}
                  </div>
                  {suggestions.length === 0 && !suggestionsLoading ? (
                    <div className="rounded-2xl bg-secondary/40 px-3 py-4 text-sm text-muted-foreground">
                      Совпадений пока нет. Попробуйте другой никнейм, username или тег.
                    </div>
                  ) : (
                    <div className="max-h-96 space-y-2 overflow-y-auto pr-1">
                      {suggestions.map((profile) => {
                        const displayName = profile.display_name || `Профиль #${profile.id}`;
                        const avatarUrl = getAvatarUrl(profile);
                        const badges = getSearchBadges(profile, searchQuery);
                        return (
                          <button
                            key={profile.id}
                            type="button"
                            onClick={() => {
                              setActiveProfileId(profile.id);
                              setSearchQuery(profile.display_name || searchQuery);
                            }}
                            className="group flex w-full items-start gap-3 rounded-2xl border border-border px-3 py-3 text-left transition-all hover:border-primary/30 hover:bg-secondary/45"
                          >
                            <Avatar className="mt-0.5 h-12 w-12 shrink-0 ring-1 ring-primary/10">
                              <AvatarImage src={avatarUrl} alt={displayName} className="object-cover" />
                              <AvatarFallback className="bg-primary text-white font-semibold">{getInitial(displayName)}</AvatarFallback>
                            </Avatar>
                            <div className="min-w-0 flex-1">
                              <div className="flex flex-wrap items-start justify-between gap-2">
                                <div className="min-w-0">
                                  <div className="truncate font-semibold text-foreground">{highlightText(displayName, searchQuery)}</div>
                                  <div className="mt-1 truncate text-sm text-muted-foreground">
                                    {profile.specialization ? highlightText(profile.specialization, searchQuery) : `Профиль #${profile.id}`}
                                  </div>
                                </div>
                                <span className="inline-flex items-center gap-1 rounded-full bg-primary/8 px-2 py-1 text-[11px] font-medium text-primary">
                                  <Sparkles className="h-3 w-3" /> выбрать
                                </span>
                              </div>
                              {profile.bio ? <p className="mt-2 line-clamp-2 text-xs text-muted-foreground">{highlightText(profile.bio, searchQuery)}</p> : null}
                              <div className="mt-2 flex flex-wrap gap-1.5">
                                {badges.map((badge) => (
                                  <span key={badge} className="rounded-full bg-primary/8 px-2 py-1 text-[11px] text-primary">{badge}</span>
                                ))}
                                {(profile.skills || []).slice(0, 4).map((skill) => (
                                  <span key={skill} className="rounded-full bg-secondary px-2 py-1 text-[11px] text-secondary-foreground">{highlightText(skill, searchQuery)}</span>
                                ))}
                              </div>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              ) : null}
            </div>

            {activeProfileId ? (
              <div className="mt-4 flex flex-wrap items-center gap-3 rounded-2xl bg-secondary/35 px-4 py-3 text-sm text-muted-foreground">
                <span>Выбран конкретный профиль из подсказок.</span>
                <button
                  type="button"
                  onClick={() => setActiveProfileId(null)}
                  className="font-medium text-primary hover:underline"
                >
                  Показать все совпадения
                </button>
              </div>
            ) : null}
          </div>

          <TagSearchFilter
            title="Теги профиля"
            subtitle="Теги учитываются без регистра. Можно искать через строку или быстро отмечать популярные теги."
            placeholder="Например: python, ml, typescript"
            selectedTags={selectedTags}
            onChange={setSelectedTags}
            availableTags={availableTags}
          />
        </div>

        {loading ? (
          <div className="py-20 text-center">
            <div className="inline-block h-12 w-12 animate-spin rounded-full border-b-2 border-primary"></div>
            <p className="mt-4 text-muted-foreground">Загрузка людей...</p>
          </div>
        ) : profiles.length === 0 ? (
          <div className="rounded-3xl border border-border bg-white px-6 py-14 text-center shadow-sm">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-secondary">
              <UsersRound className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="mb-2 text-xl font-semibold text-foreground">Ничего не найдено</h3>
            <p className="text-muted-foreground">Попробуйте изменить поисковый запрос или убрать часть тегов.</p>
          </div>
        ) : (
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {profiles.map((profile) => {
              const displayName = profile.display_name || `Профиль #${profile.id}`;
              const avatarUrl = getAvatarUrl(profile);
              return (
                <Link
                  key={profile.id}
                  to={`/profiles/${profile.id}`}
                  className="group rounded-3xl border border-border bg-white p-5 shadow-sm transition-all hover:-translate-y-1 hover:border-primary/25 hover:shadow-lg"
                >
                  <div className="flex items-start gap-4">
                    <Avatar className="h-14 w-14 shrink-0 ring-2 ring-primary/10">
                      <AvatarImage src={avatarUrl} alt={displayName} className="object-cover" />
                      <AvatarFallback className="bg-primary text-white font-semibold">{getInitial(displayName)}</AvatarFallback>
                    </Avatar>
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-lg font-semibold text-foreground transition-colors group-hover:text-primary">{displayName}</div>
                      <div className="mt-1 truncate text-sm text-muted-foreground">{profile.specialization || `Профиль #${profile.id}`}</div>
                    </div>
                  </div>

                  {profile.bio ? <p className="mt-4 line-clamp-3 text-sm text-muted-foreground">{profile.bio}</p> : null}

                  <div className="mt-4 flex flex-wrap gap-2">
                    {(profile.skills || []).slice(0, 5).map((skill) => (
                      <span key={skill} className="rounded-full bg-secondary px-3 py-1 text-xs font-medium text-secondary-foreground">
                        {skill}
                      </span>
                    ))}
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
