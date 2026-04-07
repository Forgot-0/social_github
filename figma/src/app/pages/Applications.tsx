import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  CheckCircle,
  XCircle,
  Clock,
  User,
  Briefcase,
  Calendar,
  Search,
  Inbox,
  SendHorizontal,
} from 'lucide-react';
import { api } from '../lib/api';
import { toast } from 'sonner';
import { useAuth } from '../contexts/AuthContext';
import { normalizeFilterValue } from '../components/TagSearchFilter';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { StyledSelect } from '../components/StyledSelect';

interface Application {
  id: string;
  project_id: number;
  position_id: string;
  candidate_id: number;
  status: 'pending' | 'accepted' | 'rejected';
  message: string;
  decided_by: number | null;
  decided_at: string | null;
  created_at?: string;
  candidate?: {
    username?: string;
    email?: string;
  };
  position?: {
    title?: string;
    required_skills?: string[];
  };
  project?: {
    name?: string;
  };
}

type ViewMode = 'mine' | 'incoming';
type StatusFilter = 'all' | 'pending' | 'accepted' | 'rejected';

function getStatusColor(status: string) {
  switch (status) {
    case 'pending':
      return 'text-amber-700 bg-amber-50 border border-amber-200';
    case 'accepted':
      return 'text-emerald-700 bg-emerald-50 border border-emerald-200';
    case 'rejected':
      return 'text-rose-700 bg-rose-50 border border-rose-200';
    default:
      return 'text-gray-700 bg-gray-50 border border-gray-200';
  }
}

function getStatusLabel(status: string) {
  switch (status) {
    case 'pending':
      return 'На рассмотрении';
    case 'accepted':
      return 'Одобрена';
    case 'rejected':
      return 'Отклонена';
    default:
      return status;
  }
}

function getStatusIcon(status: string) {
  switch (status) {
    case 'pending':
      return <Clock className="h-4 w-4" />;
    case 'accepted':
      return <CheckCircle className="h-4 w-4" />;
    case 'rejected':
      return <XCircle className="h-4 w-4" />;
    default:
      return <Clock className="h-4 w-4" />;
  }
}

function normalizeApplication(application: any): Application {
  return {
    ...application,
    message: application?.message || '',
    position: application?.position || {},
    project: application?.project || {},
    candidate: application?.candidate || {},
  };
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

export function Applications() {
  const { user } = useAuth();
  const [viewMode, setViewMode] = useState<ViewMode>('mine');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [applications, setApplications] = useState<Application[]>([]);
  const [candidateProfiles, setCandidateProfiles] = useState<Record<number, any>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      void loadApplications();
    }, 250);

    return () => window.clearTimeout(timeout);
  }, [viewMode, statusFilter]);

  useEffect(() => {
    const candidateIds = Array.from(new Set(applications.map((application) => application.candidate_id).filter(Boolean)));
    if (candidateIds.length === 0) {
      setCandidateProfiles({});
      return;
    }

    let cancelled = false;
    const loadProfiles = async () => {
      const results = await Promise.allSettled(candidateIds.map((candidateId) => api.getProfile(candidateId)));
      if (cancelled) return;
      const nextProfiles: Record<number, any> = {};
      results.forEach((result, index) => {
        if (result.status === 'fulfilled') {
          nextProfiles[candidateIds[index]] = result.value;
        }
      });
      setCandidateProfiles(nextProfiles);
    };

    void loadProfiles();
    return () => {
      cancelled = true;
    };
  }, [applications]);

  const loadApplications = async () => {
    if (!user) return;

    try {
      setLoading(true);
      const params = {
        page: 1,
        page_size: 100,
        sort: 'created_at:desc',
        status: statusFilter !== 'all' ? statusFilter : undefined,
      };

      const data = viewMode === 'mine' ? await api.getMyApplications(params) : await api.getApplications(params);
      const items = Array.isArray(data?.items) ? data.items : [];
      setApplications(items.map(normalizeApplication));
    } catch (error: any) {
      console.error('Failed to load applications:', error);
      toast.error(error?.error?.message || 'Ошибка загрузки заявок');
      setApplications([]);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (applicationId: string) => {
    try {
      await api.approveApplication(applicationId);
      toast.success('Заявка одобрена');
      await loadApplications();
    } catch (error: any) {
      console.error('Failed to approve:', error);
      toast.error(error?.error?.message || 'Ошибка одобрения заявки');
    }
  };

  const handleReject = async (applicationId: string) => {
    try {
      await api.rejectApplication(applicationId);
      toast.success('Заявка отклонена');
      await loadApplications();
    } catch (error: any) {
      console.error('Failed to reject:', error);
      toast.error(error?.error?.message || 'Ошибка отклонения заявки');
    }
  };

  const filteredApplications = useMemo(() => {
    const normalizedSearch = normalizeFilterValue(searchQuery);
    if (!normalizedSearch) return applications;

    return applications.filter((application) => {
      const profile = candidateProfiles[application.candidate_id];
      const haystack = [
        application.position?.title,
        application.project?.name,
        profile?.display_name,
        application.candidate?.username,
        application.candidate?.email,
        application.message,
      ]
        .filter(Boolean)
        .map((value) => normalizeFilterValue(String(value)))
        .join(' ');

      return haystack.includes(normalizedSearch);
    });
  }, [applications, candidateProfiles, searchQuery]);

  const stats = {
    total: applications.length,
    pending: applications.filter((item) => item.status === 'pending').length,
    accepted: applications.filter((item) => item.status === 'accepted').length,
    rejected: applications.filter((item) => item.status === 'rejected').length,
  };

  if (loading) {
    return (
      <div className="py-20 text-center">
        <div className="inline-block h-12 w-12 animate-spin rounded-full border-b-2 border-primary"></div>
        <p className="mt-4 text-muted-foreground">Загрузка заявок...</p>
      </div>
    );
  }

  return (
    <div className="py-12">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="mb-8 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="mb-4 text-3xl font-bold text-foreground md:text-4xl">Отклики</h1>
            <p className="text-lg text-muted-foreground">Карточки откликов связаны с профилями кандидатов и проектами.</p>
          </div>
          <div className="inline-flex rounded-2xl border border-border bg-white p-1 shadow-sm">
            <button
              onClick={() => setViewMode('mine')}
              className={`inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm transition-colors ${
                viewMode === 'mine' ? 'bg-primary text-white' : 'text-muted-foreground hover:bg-secondary'
              }`}
            >
              <SendHorizontal className="h-4 w-4" />
              <span>Мои отклики</span>
            </button>
            <button
              onClick={() => setViewMode('incoming')}
              className={`inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm transition-colors ${
                viewMode === 'incoming' ? 'bg-primary text-white' : 'text-muted-foreground hover:bg-secondary'
              }`}
            >
              <Inbox className="h-4 w-4" />
              <span>Входящие</span>
            </button>
          </div>
        </div>

        <div className="mb-6 grid gap-4 md:grid-cols-4">
          <div className="rounded-2xl border border-border bg-white p-4 shadow-sm">
            <div className="text-2xl font-bold text-foreground">{stats.total}</div>
            <div className="text-sm text-muted-foreground">Всего</div>
          </div>
          <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 shadow-sm">
            <div className="text-2xl font-bold text-amber-700">{stats.pending}</div>
            <div className="text-sm text-amber-700">На рассмотрении</div>
          </div>
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 shadow-sm">
            <div className="text-2xl font-bold text-emerald-700">{stats.accepted}</div>
            <div className="text-sm text-emerald-700">Одобрено</div>
          </div>
          <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 shadow-sm">
            <div className="text-2xl font-bold text-rose-700">{stats.rejected}</div>
            <div className="text-sm text-rose-700">Отклонено</div>
          </div>
        </div>

        <div className="mb-6 rounded-2xl border border-border bg-white p-5 shadow-sm">
          <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_220px]">
            <div>
              <label className="mb-2 block text-sm font-semibold text-foreground">Поиск</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder={viewMode === 'mine' ? 'По позиции, проекту или сообщению...' : 'По кандидату, проекту или позиции...'}
                  className="app-input w-full pl-10 pr-4"
                />
              </div>
            </div>
            <div>
              <label className="mb-2 block text-sm font-semibold text-foreground">Статус</label>
              <StyledSelect
                value={statusFilter}
                onChange={(value) => setStatusFilter(value as StatusFilter)}
                options={[
                  { value: 'all', label: 'Все статусы' },
                  { value: 'pending', label: 'На рассмотрении' },
                  { value: 'accepted', label: 'Одобренные' },
                  { value: 'rejected', label: 'Отклоненные' },
                ]}
              />
            </div>
          </div>
        </div>

        {filteredApplications.length === 0 ? (
          <div className="rounded-2xl border border-border bg-white px-6 py-12 text-center shadow-sm">
            <h3 className="mb-2 text-xl font-semibold">Заявки не найдены</h3>
            <p className="text-muted-foreground">Попробуйте изменить фильтры или поисковый запрос.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredApplications.map((application) => {
              const profile = candidateProfiles[application.candidate_id];
              const candidateName = profile?.display_name || application.candidate?.username || `Пользователь #${application.candidate_id}`;
              const avatarUrl = getAvatarUrl(profile);

              return (
                <div key={application.id} className="rounded-2xl border border-border bg-white p-6 shadow-sm">
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                    <div className="flex-1">
                      <div className="mb-3 flex flex-wrap items-center gap-3">
                        <span className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-sm ${getStatusColor(application.status)}`}>
                          {getStatusIcon(application.status)}
                          <span>{getStatusLabel(application.status)}</span>
                        </span>
                        <span className="inline-flex items-center gap-1 text-sm text-muted-foreground">
                          <Calendar className="h-4 w-4" />
                          {application.created_at ? new Date(application.created_at).toLocaleDateString('ru-RU') : 'Без даты'}
                        </span>
                      </div>

                      <div className="mb-4 grid gap-3 md:grid-cols-2">
                        <div className="rounded-xl bg-secondary/40 p-4">
                          <div className="mb-1 flex items-center gap-2 text-sm font-medium text-foreground">
                            <Briefcase className="h-4 w-4" />
                            <span>Проект и позиция</span>
                          </div>
                          <Link to={`/projects/${application.project_id}`} className="block font-semibold text-foreground transition-colors hover:text-primary">
                            {application.position?.title || `Позиция #${application.position_id}`}
                          </Link>
                          <Link to={`/projects/${application.project_id}`} className="mt-1 inline-block text-sm text-primary hover:underline">
                            {application.project?.name || `Проект #${application.project_id}`}
                          </Link>
                        </div>

                        <Link to={`/profiles/${application.candidate_id}`} className="rounded-xl bg-secondary/40 p-4 transition-colors hover:bg-secondary/60">
                          <div className="mb-2 flex items-center gap-2 text-sm font-medium text-foreground">
                            <User className="h-4 w-4" />
                            <span>{viewMode === 'mine' ? 'Профиль кандидата' : 'Профиль кандидата'}</span>
                          </div>
                          <div className="flex items-center gap-3">
                            <Avatar className="h-11 w-11 ring-2 ring-primary/10">
                              <AvatarImage src={avatarUrl} alt={candidateName} className="object-cover" />
                              <AvatarFallback className="bg-primary text-white font-semibold">
                                {getInitial(candidateName)}
                              </AvatarFallback>
                            </Avatar>
                            <div className="min-w-0">
                              <div className="truncate font-semibold text-foreground">{candidateName}</div>
                              {application.candidate?.email ? (
                                <div className="truncate text-sm text-muted-foreground">{application.candidate.email}</div>
                              ) : (
                                <div className="text-sm text-primary">Открыть профиль</div>
                              )}
                            </div>
                          </div>
                        </Link>
                      </div>

                      {application.position?.required_skills?.length ? (
                        <div className="mb-4 flex flex-wrap gap-2">
                          {application.position.required_skills.map((skill) => (
                            <span key={skill} className="rounded-full bg-secondary px-3 py-1 text-xs text-secondary-foreground">
                              {skill}
                            </span>
                          ))}
                        </div>
                      ) : null}

                      {application.message ? (
                        <div className="rounded-xl border border-border bg-secondary/20 p-4">
                          <div className="mb-1 text-sm font-medium text-foreground">Сообщение</div>
                          <p className="text-sm leading-relaxed text-muted-foreground">{application.message}</p>
                        </div>
                      ) : null}
                    </div>

                    {viewMode === 'incoming' && application.status === 'pending' ? (
                      <div className="flex flex-col gap-2 lg:w-44">
                        <button
                          onClick={() => handleApprove(application.id)}
                          className="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-600 px-4 py-3 text-white transition-colors hover:bg-emerald-700"
                        >
                          <CheckCircle className="h-4 w-4" />
                          <span>Одобрить</span>
                        </button>
                        <button
                          onClick={() => handleReject(application.id)}
                          className="inline-flex items-center justify-center gap-2 rounded-xl bg-rose-600 px-4 py-3 text-white transition-colors hover:bg-rose-700"
                        >
                          <XCircle className="h-4 w-4" />
                          <span>Отклонить</span>
                        </button>
                      </div>
                    ) : null}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}