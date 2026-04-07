import { useState, useEffect, useMemo } from "react";
import { UserPlus, Shield, X, Trash2, Save, Search, Loader2, CheckCircle2, Sparkles } from "lucide-react";
import { Link } from 'react-router-dom';
import { api } from "../lib/api";
import { toast } from "sonner";
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar";
import { StyledSelect } from "./StyledSelect";

interface TeamMember {
  user_id: number;
  username: string;
  role?: string | { id?: number; name?: string };
  role_id?: number;
  permissions?: string[];
  status?: string;
}

interface TeamManagerProps {
  projectId: number;
  members: TeamMember[];
  onUpdate: () => void;
  isOwner: boolean;
  currentUserId?: number | null;
}

function getAvatarUrl(profile: any) {
  const avatars = profile?.avatars;
  if (!avatars || typeof avatars !== 'object') return '';
  const preferred = avatars['128'] || avatars['256'] || avatars.small || avatars.medium || avatars.large;
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

function normalize(value?: string | null) {
  return String(value || '').trim().toLowerCase();
}

function resolveRoleId(member: TeamMember, roles: any[]) {
  if (typeof member.role_id === 'number') return member.role_id;
  const roleName = typeof member.role === 'string' ? member.role : member.role?.name;
  if (!roleName) return 0;
  const matchedRole = roles.find((role) => String(role.name).toLowerCase() === String(roleName).toLowerCase());
  return matchedRole?.id || 0;
}

function resolveRoleName(member: TeamMember, roles: any[]) {
  if (typeof member.role === 'string') return member.role;
  if (member.role?.name) return member.role.name;
  const roleId = resolveRoleId(member, roles);
  const matchedRole = roles.find((role) => role.id === roleId);
  return matchedRole?.name || 'member';
}

function formatStatus(status?: string) {
  if (!status) return '';

  const normalized = String(status).trim().toLowerCase();
  if (normalized === 'pending') return 'ожидает принятия';
  if (normalized === 'accepted' || normalized === 'active') return 'в команде';
  if (normalized === 'rejected') return 'отклонён';
  return status;
}

function getRoleBadgeClass(roleName: string) {
  const normalized = normalize(roleName);
  if (normalized === 'owner') return 'border-violet-200 bg-violet-50 text-slate-600';
  if (normalized === 'admin') return 'border-sky-200 bg-sky-50 text-slate-600';
  if (normalized === 'member') return 'border-emerald-200 bg-emerald-50 text-slate-600';
  if (normalized === 'viewer') return 'border-amber-200 bg-amber-50 text-slate-600';
  return 'border-teal-200 bg-teal-50 text-slate-600';
}

function getStatusBadgeClass(status?: string) {
  const normalized = normalize(status);
  if (normalized === 'pending') return 'border-slate-200 bg-slate-100 text-slate-500';
  if (normalized === 'accepted' || normalized === 'active') return 'border-emerald-100 bg-emerald-50 text-slate-500';
  if (normalized === 'rejected') return 'border-rose-200 bg-rose-50 text-slate-500';
  return 'border-slate-200 bg-slate-100 text-slate-500';
}

function mergeProfileSearchResults(results: any[]) {
  const map = new Map<number, any>();
  results.forEach((result) => {
    const items = Array.isArray(result?.items) ? result.items : [];
    items.forEach((profile: any) => {
      if (typeof profile?.id === 'number' && !map.has(profile.id)) {
        map.set(profile.id, profile);
      }
    });
  });
  return Array.from(map.values());
}

function scoreProfile(profile: any, query: string) {
  const q = normalize(query);
  if (!q) return 0;

  const displayName = normalize(profile?.display_name);
  const specialization = normalize(profile?.specialization);
  const bio = normalize(profile?.bio);
  const skills = Array.isArray(profile?.skills) ? profile.skills.map((skill: string) => normalize(skill)) : [];

  let score = 0;
  if (displayName.startsWith(q)) score += 140;
  else if (displayName.includes(q)) score += 95;

  if (specialization.startsWith(q)) score += 70;
  else if (specialization.includes(q)) score += 45;

  skills.forEach((skill) => {
    if (skill === q) score += 90;
    else if (skill.startsWith(q)) score += 65;
    else if (skill.includes(q)) score += 40;
  });

  if (bio.includes(q)) score += 20;
  return score;
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

function getMatchReasons(profile: any, query: string) {
  const q = normalize(query);
  const reasons: string[] = [];
  if (!q) return reasons;

  if (normalize(profile?.display_name).includes(q)) reasons.push('имя');
  if (normalize(profile?.specialization).includes(q)) reasons.push('специализация');
  const matchedSkill = Array.isArray(profile?.skills)
    ? profile.skills.find((skill: string) => normalize(skill).includes(q))
    : null;
  if (matchedSkill) reasons.push(`навык: ${matchedSkill}`);
  return reasons.slice(0, 2);
}

export function TeamManager({ projectId, members, onUpdate, isOwner, currentUserId }: TeamManagerProps) {
  const [showInviteForm, setShowInviteForm] = useState(false);
  const [roles, setRoles] = useState<any[]>([]);
  const [profiles, setProfiles] = useState<Record<number, any>>({});
  const [roleDrafts, setRoleDrafts] = useState<Record<number, number>>({});
  const [inviteData, setInviteData] = useState({ role_id: 0 });
  const [searchQuery, setSearchQuery] = useState('');
  const [profileResults, setProfileResults] = useState<any[]>([]);
  const [selectedProfile, setSelectedProfile] = useState<any | null>(null);
  const [searchingProfiles, setSearchingProfiles] = useState(false);
  const [savingMemberId, setSavingMemberId] = useState<number | null>(null);
  const [removingMemberId, setRemovingMemberId] = useState<number | null>(null);

  useEffect(() => {
    if (isOwner || showInviteForm) {
      void loadRoles();
    }
  }, [isOwner, showInviteForm]);

  useEffect(() => {
    const nextDrafts: Record<number, number> = {};
    members.forEach((member) => {
      nextDrafts[member.user_id] = resolveRoleId(member, roles);
    });
    setRoleDrafts(nextDrafts);
  }, [members, roles]);

  useEffect(() => {
    const uniqueIds = Array.from(new Set(members.map((member) => member.user_id)));
    if (uniqueIds.length === 0) {
      setProfiles({});
      return;
    }

    let cancelled = false;

    const loadProfiles = async () => {
      const results = await Promise.allSettled(uniqueIds.map((userId) => api.getProfile(userId)));
      if (cancelled) return;

      const nextProfiles: Record<number, any> = {};
      results.forEach((result, index) => {
        if (result.status === 'fulfilled') {
          nextProfiles[uniqueIds[index]] = result.value;
        }
      });
      setProfiles(nextProfiles);
    };

    void loadProfiles();
    return () => {
      cancelled = true;
    };
  }, [members]);

  useEffect(() => {
    if (!showInviteForm) {
      setSearchQuery('');
      setProfileResults([]);
      setSelectedProfile(null);
      return;
    }

    const query = searchQuery.trim();
    if (!query) {
      setProfileResults([]);
      return;
    }

    let cancelled = false;
    const timeoutId = window.setTimeout(async () => {
      try {
        setSearchingProfiles(true);
        const [byDisplayName, byUsername, bySkills] = await Promise.all([
          api.getProfiles({ display_name: query, page: 1, page_size: 8, sort: 'display_name:asc' }),
          api.getProfiles({ username: query, page: 1, page_size: 8, sort: 'display_name:asc' }),
          api.getProfiles({ skills: [query], page: 1, page_size: 8, sort: 'display_name:asc' }),
        ]);

        if (cancelled) return;

        const existingMemberIds = new Set(members.map((member) => member.user_id));
        if (currentUserId) existingMemberIds.add(currentUserId);

        const merged = mergeProfileSearchResults([byDisplayName, byUsername, bySkills])
          .filter((profile) => !existingMemberIds.has(profile.id))
          .sort((left, right) => {
            const scoreDiff = scoreProfile(right, query) - scoreProfile(left, query);
            if (scoreDiff !== 0) return scoreDiff;
            return String(left.display_name || '').localeCompare(String(right.display_name || ''), 'ru');
          });

        setProfileResults(merged);
      } catch (error) {
        if (!cancelled) {
          console.error('Failed to search profiles:', error);
          setProfileResults([]);
        }
      } finally {
        if (!cancelled) {
          setSearchingProfiles(false);
        }
      }
    }, 280);

    return () => {
      cancelled = true;
      window.clearTimeout(timeoutId);
    };
  }, [showInviteForm, searchQuery, members, currentUserId]);

  const sortedMembers = useMemo(() => {
    return [...members].sort((a, b) => {
      if (a.user_id === currentUserId) return -1;
      if (b.user_id === currentUserId) return 1;
      const left = profiles[a.user_id]?.display_name || a.username || '';
      const right = profiles[b.user_id]?.display_name || b.username || '';
      return left.localeCompare(right, 'ru');
    });
  }, [members, currentUserId, profiles]);

  const loadRoles = async () => {
    try {
      const data = await api.getProjectRoles({ page: 1, page_size: 50, sort: 'name:asc' });
      const items = Array.isArray(data?.items) ? data.items : Array.isArray(data) ? data : [];
      setRoles(items);
    } catch (error: any) {
      console.error('Failed to load roles:', error);
    }
  };

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedProfile?.id) {
      toast.error('Выберите профиль для приглашения');
      return;
    }

    try {
      await api.inviteToProject(projectId, {
        user_id: selectedProfile.id,
        role_id: inviteData.role_id || undefined,
      });
      toast.success('Приглашение отправлено');
      setShowInviteForm(false);
      setInviteData({ role_id: 0 });
      setSearchQuery('');
      setProfileResults([]);
      setSelectedProfile(null);
      onUpdate();
    } catch (error: any) {
      console.error('Failed to invite:', error);
      toast.error(error?.error?.message || 'Ошибка отправки приглашения');
    }
  };

  const handleSaveRole = async (member: TeamMember) => {
    const nextRoleId = roleDrafts[member.user_id];
    if (!nextRoleId || nextRoleId === resolveRoleId(member, roles)) return;

    try {
      setSavingMemberId(member.user_id);
      await api.updateProjectMemberRole(projectId, member.user_id, nextRoleId);
      toast.success('Роль участника обновлена');
      onUpdate();
    } catch (error: any) {
      console.error('Failed to update project role:', error);
      toast.error(error?.error?.message || 'Не удалось обновить роль участника');
    } finally {
      setSavingMemberId(null);
    }
  };

  const handleRemoveMember = async (member: TeamMember) => {
    const confirmed = window.confirm(`Удалить участника ${profiles[member.user_id]?.display_name || member.username} из проекта?`);
    if (!confirmed) return;

    try {
      setRemovingMemberId(member.user_id);
      await api.removeProjectMember(projectId, member.user_id);
      toast.success('Участник удалён из проекта');
      onUpdate();
    } catch (error: any) {
      console.error('Failed to remove project member:', error);
      toast.error(error?.error?.message || 'Не удалось удалить участника');
    } finally {
      setRemovingMemberId(null);
    }
  };

  return (
    <div>
      {isOwner && !showInviteForm ? (
        <button
          onClick={() => setShowInviteForm(true)}
          className="mb-6 flex items-center space-x-2 rounded-lg bg-primary px-4 py-2 text-white transition-colors hover:bg-accent"
        >
          <UserPlus className="h-5 w-5" />
          <span>Пригласить участника</span>
        </button>
      ) : null}

      {isOwner && showInviteForm ? (
        <form onSubmit={handleInvite} className="mb-6 space-y-4 rounded-2xl bg-secondary/50 p-6">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h3 className="text-xl font-semibold">Пригласить в команду</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                Поиск идёт по профилям. Для приглашения используется ID профиля как ID пользователя.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setShowInviteForm(false)}
              className="text-muted-foreground hover:text-foreground"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium">
              Поиск профиля <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setSelectedProfile(null);
                }}
                className="app-input pl-10"
                placeholder="Имя, username, стек или навык"
                autoComplete="off"
              />
            </div>
            <p className="mt-2 text-xs text-muted-foreground">
              Умный поиск ранжирует результаты по совпадению имени, специализации и навыков.
            </p>
          </div>

          {selectedProfile ? (
            <div className="rounded-2xl border border-emerald-200 bg-emerald-50/80 p-4">
              <div className="flex items-center gap-3">
                <Avatar className="h-12 w-12 ring-2 ring-emerald-100">
                  <AvatarImage src={getAvatarUrl(selectedProfile)} alt={selectedProfile.display_name || `Профиль #${selectedProfile.id}`} />
                  <AvatarFallback className="bg-primary text-white font-semibold">
                    {getInitial(selectedProfile.display_name || `Профиль #${selectedProfile.id}`)}
                  </AvatarFallback>
                </Avatar>
                <div className="min-w-0 flex-1">
                  <div className="truncate font-semibold text-foreground">
                    {selectedProfile.display_name || `Профиль #${selectedProfile.id}`}
                  </div>
                  <div className="mt-1 truncate text-sm text-muted-foreground">
                    {selectedProfile.specialization || 'Профиль выбран для приглашения'}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedProfile(null)}
                  className="text-sm font-medium text-emerald-700 transition-colors hover:text-emerald-800"
                >
                  Сбросить
                </button>
              </div>
            </div>
          ) : null}

          {!selectedProfile && searchQuery.trim() ? (
            <div className="rounded-2xl border border-border bg-white/90 p-3 shadow-sm">
              {searchingProfiles ? (
                <div className="flex items-center gap-2 px-2 py-3 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Подбираем профили...</span>
                </div>
              ) : profileResults.length === 0 ? (
                <div className="px-2 py-3 text-sm text-muted-foreground">
                  Подходящие профили не найдены.
                </div>
              ) : (
                <div className="max-h-80 space-y-2 overflow-y-auto pr-1">
                  {profileResults.map((profile) => {
                    const displayName = profile.display_name || `Профиль #${profile.id}`;
                    const avatarUrl = getAvatarUrl(profile);
                    const reasons = getMatchReasons(profile, searchQuery);
                    return (
                      <button
                        key={profile.id}
                        type="button"
                        onClick={() => setSelectedProfile(profile)}
                        className="group flex w-full items-start gap-3 rounded-2xl border border-border px-3 py-3 text-left transition-all hover:border-primary/30 hover:bg-secondary/60"
                      >
                        <Avatar className="mt-0.5 h-12 w-12 shrink-0 ring-1 ring-primary/10">
                          <AvatarImage src={avatarUrl} alt={displayName} className="object-cover" />
                          <AvatarFallback className="bg-primary text-white font-semibold">
                            {getInitial(displayName)}
                          </AvatarFallback>
                        </Avatar>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <div className="truncate font-medium text-foreground">{highlightText(displayName, searchQuery)}</div>
                              <div className="mt-1 truncate text-sm text-muted-foreground">
                                {profile.specialization ? highlightText(profile.specialization, searchQuery) : `ID профиля: ${profile.id}`}
                              </div>
                            </div>
                            <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-primary/8 px-2 py-1 text-[11px] font-medium text-primary">
                              <Sparkles className="h-3 w-3" />
                              выбрать
                            </span>
                          </div>

                          {profile.bio ? (
                            <p className="mt-2 line-clamp-2 text-xs text-muted-foreground">
                              {highlightText(String(profile.bio), searchQuery)}
                            </p>
                          ) : null}

                          <div className="mt-2 flex flex-wrap gap-1.5">
                            {reasons.map((reason) => (
                              <span key={reason} className="rounded-full bg-primary/8 px-2 py-1 text-[11px] text-primary">
                                {reason}
                              </span>
                            ))}
                            {Array.isArray(profile.skills) && profile.skills.slice(0, 4).map((skill: string) => (
                              <span key={skill} className="rounded-full bg-secondary px-2 py-1 text-[11px] text-secondary-foreground">
                                {highlightText(skill, searchQuery)}
                              </span>
                            ))}
                          </div>
                        </div>
                        <CheckCircle2 className="mt-1 h-4 w-4 shrink-0 text-muted-foreground transition-colors group-hover:text-primary" />
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          ) : null}

          {roles.length > 0 ? (
            <div>
              <label className="mb-2 block text-sm font-medium">Роль</label>
              <StyledSelect
                value={inviteData.role_id}
                onChange={(value) => setInviteData({ ...inviteData, role_id: Number(value) })}
                options={[
                  { value: 0, label: 'Без роли' },
                  ...roles.map((role) => ({ value: role.id, label: role.name })),
                ]}
              />
            </div>
          ) : null}

          <div className="flex space-x-4">
            <button
              type="submit"
              className="flex-1 rounded-lg bg-primary py-2 text-white transition-colors hover:bg-accent disabled:cursor-not-allowed disabled:opacity-50"
              disabled={!selectedProfile}
            >
              Отправить приглашение
            </button>
            <button
              type="button"
              onClick={() => setShowInviteForm(false)}
              className="rounded-lg border border-border bg-white px-6 py-2 transition-colors hover:bg-secondary"
            >
              Отмена
            </button>
          </div>
        </form>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2">
        {sortedMembers.map((member) => {
          const profile = profiles[member.user_id];
          const displayName = profile?.display_name || member.username || `Профиль #${member.user_id}`;
          const avatarUrl = getAvatarUrl(profile);
          const roleName = resolveRoleName(member, roles);
          const currentRoleId = resolveRoleId(member, roles);
          const draftRoleId = roleDrafts[member.user_id] ?? currentRoleId;
          const canManageMember = Boolean(isOwner && member.user_id !== currentUserId);
          const isSavingRole = savingMemberId === member.user_id;
          const isRemoving = removingMemberId === member.user_id;
          const memberStatus = formatStatus(member.status);

          return (
            <div key={member.user_id} className="rounded-2xl border border-border bg-secondary/35 p-4 shadow-sm">
              <div className="flex items-start gap-3">
                <Link to={`/profiles/${member.user_id}`} className="shrink-0">
                  <Avatar className="h-12 w-12 ring-2 ring-primary/10">
                    <AvatarImage src={avatarUrl} alt={displayName} className="object-cover" />
                    <AvatarFallback className="bg-primary text-white font-semibold">
                      {getInitial(displayName)}
                    </AvatarFallback>
                  </Avatar>
                </Link>
                <div className="min-w-0 flex-1">
                  <Link to={`/profiles/${member.user_id}`} className="block truncate font-semibold text-foreground transition-colors hover:text-primary">
                    {displayName}
                  </Link>
                  <div className="mt-1 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
                    <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs shadow-sm ${getRoleBadgeClass(roleName)}`}>
                      <Shield className="h-3 w-3" />
                      {roleName}
                    </span>
                    {memberStatus ? (
                      <span className={`rounded-full border px-2.5 py-1 text-xs shadow-sm ${getStatusBadgeClass(member.status)}`}>
                        {memberStatus}
                      </span>
                    ) : null}
                  </div>
                </div>
              </div>

              {canManageMember && roles.length > 0 ? (
                <div className="mt-4 space-y-3 border-t border-border pt-4">
                  <div className="grid gap-2 sm:grid-cols-[minmax(0,1fr)_auto]">
                    <StyledSelect
                      value={draftRoleId}
                      onChange={(value) => setRoleDrafts((prev) => ({ ...prev, [member.user_id]: Number(value) }))}
                      options={[
                        { value: 0, label: 'Без роли' },
                        ...roles.map((role) => ({ value: role.id, label: role.name })),
                      ]}
                      triggerClassName="h-11"
                    />
                    <button
                      type="button"
                      onClick={() => handleSaveRole(member)}
                      disabled={draftRoleId === currentRoleId || isSavingRole}
                      className="inline-flex items-center justify-center gap-2 rounded-xl border border-primary/20 bg-white px-4 py-2 text-sm font-medium text-primary transition-colors hover:bg-secondary disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      <Save className="h-4 w-4" />
                      <span>{isSavingRole ? 'Сохранение...' : 'Сохранить роль'}</span>
                    </button>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleRemoveMember(member)}
                    disabled={isRemoving}
                    className="inline-flex items-center gap-2 text-sm font-medium text-destructive transition-colors hover:opacity-80 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <Trash2 className="h-4 w-4" />
                    <span>{isRemoving ? 'Удаление...' : 'Удалить из проекта'}</span>
                  </button>
                </div>
              ) : null}
            </div>
          );
        })}
      </div>

      {members.length === 0 && !showInviteForm ? (
        <div className="py-8 text-center text-muted-foreground">
          Нет участников. Пригласите кого-нибудь в команду!
        </div>
      ) : null}
    </div>
  );
}
