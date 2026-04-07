import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Users, Calendar, MapPin, Send, Search, Clock, ChevronDown, ChevronUp } from 'lucide-react';
import { ImageWithFallback } from '../components/figma/ImageWithFallback';
import { PositionManager } from '../components/PositionManager';
import { TeamManager } from '../components/TeamManager';
import { MarkdownContent } from '../components/MarkdownContent';
import { api } from '../lib/api';
import { toast } from 'sonner';
import { useMemo, useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { TagSearchFilter, normalizeFilterValue } from '../components/TagSearchFilter';
import { StyledSelect } from '../components/StyledSelect';

const DEFAULT_PROJECT_IMAGE =
  'data:image/svg+xml;charset=UTF-8,' +
  encodeURIComponent(`
    <svg xmlns="http://www.w3.org/2000/svg" width="1200" height="675" viewBox="0 0 1200 675">
      <rect width="1200" height="675" fill="#eef2ff"/>
      <text x="600" y="320" text-anchor="middle" font-family="Arial, sans-serif" font-size="56" fill="#334155">ИнКоллаб</text>
      <text x="600" y="390" text-anchor="middle" font-family="Arial, sans-serif" font-size="28" fill="#64748b">Project details</text>
    </svg>
  `);

const locationTypes: Record<string, string> = {
  remote: 'Удаленно',
  hybrid: 'Гибрид',
  onsite: 'Офис',
};

const loadTypes: Record<string, string> = {
  low: 'Низкая',
  medium: 'Средняя',
  high: 'Высокая',
};

function normalizeProject(project: any) {
  return {
    ...project,
    tags: Array.isArray(project?.tags) ? project.tags : [],
    memberships: Array.isArray(project?.memberships)
      ? project.memberships.map((member: any) => ({
          ...member,
          username: member?.username || `User #${member?.user_id ?? '?'}`,
        }))
      : [],
    image:
      project?.image ||
      project?.meta_data?.image ||
      project?.meta_data?.cover_image ||
      DEFAULT_PROJECT_IMAGE,
    full_description:
      project?.full_description || project?.description || 'Описание проекта пока не добавлено.',
  };
}

function normalizePosition(position: any) {
  return {
    ...position,
    title: position?.title || 'Без названия',
    description: position?.description || '',
    required_skills: Array.isArray(position?.required_skills) ? position.required_skills : [],
    is_open: Boolean(position?.is_open),
  };
}

function matchesSelectedSkills(positionSkills: string[], selectedSkills: string[]) {
  if (selectedSkills.length === 0) return true;
  const normalizedPositionSkills = positionSkills.map((skill) => normalizeFilterValue(skill));
  return selectedSkills.every((skill) => normalizedPositionSkills.includes(normalizeFilterValue(skill)));
}

export function ProjectDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const [project, setProject] = useState<any>(null);
  const [positions, setPositions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [positionsLoading, setPositionsLoading] = useState(false);
  const [titleFilter, setTitleFilter] = useState('');
  const [locationFilter, setLocationFilter] = useState('all');
  const [loadFilter, setLoadFilter] = useState('all');
  const [skillFilter, setSkillFilter] = useState<string[]>([]);
  const [descriptionExpanded, setDescriptionExpanded] = useState(false);

  const allSkills = useMemo(
    () => Array.from(new Set(positions.flatMap((position) => position.required_skills || []))).sort((a, b) => a.localeCompare(b)),
    [positions]
  );

  useEffect(() => {
    if (!id) return;
    void loadProject();
  }, [id]);

  useEffect(() => {
    if (!id) return;
    const timeout = window.setTimeout(() => {
      void loadPositions();
    }, 250);

    return () => window.clearTimeout(timeout);
  }, [id, titleFilter, locationFilter, loadFilter, skillFilter]);

  const loadProject = async () => {
    if (!id) return;

    try {
      setLoading(true);
      const data = await api.getProject(Number(id));
      setProject(normalizeProject(data));
    } catch (error: any) {
      console.error('Failed to load project:', error);
      toast.error(error?.error?.message || 'Не удалось загрузить проект из API');
      setProject(null);
    } finally {
      setLoading(false);
    }
  };

  const loadPositions = async () => {
    if (!id) return;

    try {
      setPositionsLoading(true);
      const data = await api.getProjectPositions(Number(id), {
        page: 1,
        page_size: 100,
        sort: 'title:asc',
        is_open: true,
        title: titleFilter.trim() || undefined,
        location_type: locationFilter !== 'all' ? locationFilter : undefined,
        expected_load: loadFilter !== 'all' ? loadFilter : undefined,
        required_skills: skillFilter.length ? skillFilter : undefined,
      });
      const items = Array.isArray(data?.items) ? data.items : [];
      setPositions(items.map(normalizePosition));
    } catch (error: any) {
      console.error('Failed to load positions:', error);
      toast.error(error?.error?.message || 'Не удалось загрузить позиции проекта');
      setPositions([]);
    } finally {
      setPositionsLoading(false);
    }
  };

  const handleApply = async (positionId: string) => {
    if (!user) {
      toast.error('Войдите, чтобы откликнуться на позицию');
      return;
    }

    try {
      await api.applyToPosition(positionId);
      toast.success('Заявка отправлена!');
    } catch (error: any) {
      console.error('Failed to apply:', error);
      toast.error(error?.error?.message || 'Ошибка отправки заявки');
    }
  };

  const isOwner = Boolean(user && project && project.owner_id === user.id);
  const descriptionText = project?.full_description || '';
  const isLongDescription = descriptionText.length > 550;

  const filteredPositions = useMemo(() => {
    const normalizedSearch = normalizeFilterValue(titleFilter);
    return positions.filter((position) => {
      const matchesSearch = !normalizedSearch || normalizeFilterValue(position.title).includes(normalizedSearch);
      const matchesLocation = locationFilter === 'all' || normalizeFilterValue(position.location_type) === normalizeFilterValue(locationFilter);
      const matchesLoad = loadFilter === 'all' || normalizeFilterValue(position.expected_load) === normalizeFilterValue(loadFilter);
      const matchesSkills = matchesSelectedSkills(position.required_skills, skillFilter);
      return matchesSearch && matchesLocation && matchesLoad && matchesSkills;
    });
  }, [positions, titleFilter, locationFilter, loadFilter, skillFilter]);

  const clearPositionFilters = () => {
    setTitleFilter('');
    setLocationFilter('all');
    setLoadFilter('all');
    setSkillFilter([]);
  };

  if (loading) {
    return (
      <div className="py-20 text-center">
        <div className="inline-block h-12 w-12 animate-spin rounded-full border-b-2 border-primary"></div>
        <p className="mt-4 text-muted-foreground">Загрузка проекта...</p>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="py-20 text-center">
        <h2 className="mb-4 text-2xl font-bold">Проект не найден</h2>
        <p className="mb-4 text-muted-foreground">Проверьте id проекта или доступ к API.</p>
        <Link to="/projects" className="text-primary hover:underline">
          Вернуться к списку проектов
        </Link>
      </div>
    );
  }

  return (
    <div className="py-12">
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        <Link
          to="/projects"
          className="mb-6 inline-flex items-center space-x-2 text-muted-foreground transition-colors hover:text-primary"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Назад к проектам</span>
        </Link>

        <div className="mb-8 overflow-hidden rounded-xl border border-border bg-white shadow-sm">
          <div className="aspect-video bg-muted">
            <ImageWithFallback src={project.image} alt={project.name} className="h-full w-full object-cover" />
          </div>
          <div className="p-8">
            <h1 className="mb-4 text-3xl font-bold md:text-4xl">{project.name}</h1>
            <p className="mb-6 text-lg text-muted-foreground">{project.small_description}</p>

            <div className="mb-6 flex flex-wrap gap-3">
              {project.tags.map((tag: string) => (
                <Link
                  key={tag}
                  to={`/projects?tags=${encodeURIComponent(tag)}`}
                  className="rounded-full bg-secondary px-4 py-2 text-secondary-foreground transition-colors hover:bg-primary hover:text-white"
                >
                  {tag}
                </Link>
              ))}
            </div>

            <div className="flex flex-wrap gap-6 text-sm text-muted-foreground">
              <div className="flex items-center space-x-2">
                <Users className="h-4 w-4" />
                <span>{project.memberships.length} участников</span>
              </div>
              <div className="flex items-center space-x-2">
                <Calendar className="h-4 w-4" />
                <span>Создан {new Date(project.created_at).toLocaleDateString('ru-RU')}</span>
              </div>
              <div className="flex items-center space-x-2">
                <MapPin className="h-4 w-4" />
                <span>Формат зависит от позиций проекта</span>
              </div>
            </div>
          </div>
        </div>

        <div className="mb-8 rounded-xl border border-border bg-white p-8 shadow-sm">
          <div className="mb-4 flex items-center justify-between gap-4">
            <h2 className="text-2xl font-bold">О проекте</h2>
            <span className="rounded-full bg-secondary px-3 py-1 text-xs text-secondary-foreground">
              Поддерживается Markdown
            </span>
          </div>

          <div className="relative">
            <div className={!descriptionExpanded && isLongDescription ? 'max-h-[22rem] overflow-hidden' : ''}>
              <MarkdownContent content={project.full_description} className="text-base" />
            </div>
            {!descriptionExpanded && isLongDescription ? (
              <div className="pointer-events-none absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-white to-transparent" />
            ) : null}
          </div>

          {isLongDescription ? (
            <button
              type="button"
              onClick={() => setDescriptionExpanded((prev) => !prev)}
              className="mt-5 inline-flex items-center gap-2 rounded-full border border-border bg-secondary/50 px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-secondary"
            >
              {descriptionExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              <span>{descriptionExpanded ? 'Свернуть описание' : 'Развернуть описание'}</span>
            </button>
          ) : null}
        </div>

        <div className="mb-8 rounded-xl border border-border bg-white p-8 shadow-sm">
          <h2 className="mb-6 text-2xl font-bold">Команда</h2>
          <TeamManager
            projectId={Number(id)}
            members={project.memberships}
            onUpdate={loadProject}
            isOwner={isOwner}
            currentUserId={user?.id}
          />
        </div>

        <div className="rounded-xl border border-border bg-white p-8 shadow-sm">
          <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-2xl font-bold">Открытые позиции</h2>
              {!isOwner ? (
                <p className="mt-2 text-sm text-muted-foreground">Фильтры позиций проекта синхронизированы с API: title, required_skills, location_type, expected_load.</p>
              ) : null}
            </div>
            {!isOwner && (titleFilter || locationFilter !== 'all' || loadFilter !== 'all' || skillFilter.length > 0) ? (
              <button onClick={clearPositionFilters} className="text-sm font-medium text-primary hover:underline">
                Сбросить фильтры
              </button>
            ) : null}
          </div>

          {isOwner ? (
            <PositionManager
              projectId={Number(id)}
              positions={positions}
              onUpdate={loadPositions}
              isOwner={isOwner}
            />
          ) : (
            <>
              <div className="mb-6 space-y-4">
                <div className="rounded-2xl border border-border bg-secondary/20 p-5">
                  <div className="grid gap-4 lg:grid-cols-[minmax(0,1.4fr)_220px_220px]">
                    <div>
                      <label className="mb-2 block text-sm font-semibold text-foreground">Поиск по названию позиции</label>
                      <div className="relative">
                        <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
                        <input
                          type="text"
                          value={titleFilter}
                          onChange={(e) => setTitleFilter(e.target.value)}
                          placeholder="Например: backend developer"
                          className="app-input w-full pl-10 pr-4"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="mb-2 block text-sm font-semibold text-foreground">Формат работы</label>
                      <StyledSelect
                        value={locationFilter}
                        onChange={setLocationFilter}
                        options={[
                          { value: 'all', label: 'Все форматы' },
                          { value: 'remote', label: 'Удаленно' },
                          { value: 'hybrid', label: 'Гибрид' },
                          { value: 'onsite', label: 'Офис' },
                        ]}
                      />
                    </div>

                    <div>
                      <label className="mb-2 block text-sm font-semibold text-foreground">Нагрузка</label>
                      <StyledSelect
                        value={loadFilter}
                        onChange={setLoadFilter}
                        options={[
                          { value: 'all', label: 'Любая нагрузка' },
                          { value: 'low', label: 'Низкая' },
                          { value: 'medium', label: 'Средняя' },
                          { value: 'high', label: 'Высокая' },
                        ]}
                      />
                    </div>
                  </div>
                </div>

                <TagSearchFilter
                  title="Навыки для позиций проекта"
                  subtitle="Выбранные навыки отправляются в API параметром required_skills."
                  placeholder="Например: python, typescript, ml"
                  selectedTags={skillFilter}
                  onChange={setSkillFilter}
                  availableTags={allSkills}
                />
              </div>

              {positionsLoading ? (
                <div className="py-10 text-center">
                  <div className="inline-block h-10 w-10 animate-spin rounded-full border-b-2 border-primary"></div>
                  <p className="mt-4 text-muted-foreground">Загрузка позиций...</p>
                </div>
              ) : filteredPositions.length === 0 ? (
                <p className="text-muted-foreground">Нет открытых позиций по текущим фильтрам</p>
              ) : (
                <div className="space-y-4">
                  {filteredPositions.map((position) => (
                    <div key={position.id} className="rounded-lg border border-border p-6">
                      <div className="mb-2 flex flex-wrap items-center gap-3">
                        <h3 className="text-xl font-semibold">{position.title}</h3>
                        <span className="rounded-full bg-secondary px-3 py-1 text-xs text-secondary-foreground">
                          {locationTypes[position.location_type] || position.location_type}
                        </span>
                        <span className="inline-flex items-center gap-1 rounded-full bg-secondary px-3 py-1 text-xs text-secondary-foreground">
                          <Clock className="h-3.5 w-3.5" />
                          {loadTypes[position.expected_load] || position.expected_load}
                        </span>
                      </div>
                      <p className="mb-3 text-muted-foreground">{position.description}</p>
                      <div className="mb-4 flex flex-wrap gap-2">
                        {position.required_skills.map((skill: string) => (
                          <span key={skill} className="rounded-full bg-secondary px-3 py-1 text-sm text-secondary-foreground">
                            {skill}
                          </span>
                        ))}
                      </div>
                      <button
                        onClick={() => handleApply(position.id)}
                        className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2 text-white transition-colors hover:bg-accent"
                      >
                        <Send className="h-4 w-4" />
                        <span>Откликнуться</span>
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}