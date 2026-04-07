import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { Search, Users, Calendar, Plus } from 'lucide-react';
import { ImageWithFallback } from '../components/figma/ImageWithFallback';
import { api } from '../lib/api';
import { toast } from 'sonner';
import { TagSearchFilter, normalizeFilterValue } from '../components/TagSearchFilter';

interface Project {
  id: number;
  owner_id: number;
  name: string;
  slug: string;
  small_description: string;
  full_description?: string;
  visibility: string;
  tags: string[];
  created_at: string;
  memberships: Array<{ user_id: number; role: string; username?: string }>;
  image?: string;
  meta_data?: Record<string, any>;
}

const DEFAULT_PROJECT_IMAGE =
  'data:image/svg+xml;charset=UTF-8,' +
  encodeURIComponent(`
    <svg xmlns="http://www.w3.org/2000/svg" width="1200" height="675" viewBox="0 0 1200 675">
      <rect width="1200" height="675" fill="#eef2ff"/>
      <circle cx="980" cy="120" r="120" fill="#dbeafe"/>
      <circle cx="180" cy="560" r="160" fill="#e0e7ff"/>
      <text x="600" y="320" text-anchor="middle" font-family="Arial, sans-serif" font-size="56" fill="#334155">ИнКоллаб</text>
      <text x="600" y="390" text-anchor="middle" font-family="Arial, sans-serif" font-size="28" fill="#64748b">Project cover</text>
    </svg>
  `);

function getProjectImage(project: Project) {
  return project.image || project.meta_data?.image || project.meta_data?.cover_image || DEFAULT_PROJECT_IMAGE;
}

function normalizeProject(project: any): Project {
  return {
    ...project,
    small_description: project?.small_description || '',
    tags: Array.isArray(project?.tags) ? project.tags : [],
    memberships: Array.isArray(project?.memberships) ? project.memberships : [],
    image: getProjectImage(project),
  };
}

function matchesSelectedTags(projectTags: string[], selectedTags: string[]) {
  if (selectedTags.length === 0) return true;
  const normalizedProjectTags = projectTags.map((tag) => normalizeFilterValue(tag));
  return selectedTags.every((tag) => normalizedProjectTags.includes(normalizeFilterValue(tag)));
}

export function Projects() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const initialSearch = searchParams.get('search') || '';
  const initialTags = searchParams.getAll('tags');

  const [searchQuery, setSearchQuery] = useState(initialSearch);
  const [selectedTags, setSelectedTags] = useState<string[]>(initialTags);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  const allTags = useMemo(
    () => Array.from(new Set(projects.flatMap((project) => project.tags))).sort((a, b) => a.localeCompare(b)),
    [projects]
  );

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      const nextParams = new URLSearchParams();
      if (searchQuery.trim()) nextParams.set('search', searchQuery.trim());
      selectedTags.forEach((tag) => nextParams.append('tags', tag));
      setSearchParams(nextParams, { replace: true });
      void loadProjects();
    }, 250);

    return () => window.clearTimeout(timeout);
  }, [searchQuery, selectedTags]);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const data = await api.getProjects({
        page: 1,
        page_size: 100,
        sort: 'created_at:desc',
        name: searchQuery.trim() || undefined,
        tags: selectedTags.length ? selectedTags : undefined,
      });
      const items = Array.isArray(data?.items) ? data.items : [];
      setProjects(items.map(normalizeProject));
    } catch (error: any) {
      console.error('Failed to load projects:', error);
      toast.error(error?.error?.message || 'Не удалось загрузить проекты из API');
      setProjects([]);
    } finally {
      setLoading(false);
    }
  };

  const filteredProjects = useMemo(() => {
    const normalizedSearch = normalizeFilterValue(searchQuery);

    return projects.filter((project) => {
      const matchesSearch =
        !normalizedSearch ||
        normalizeFilterValue(project.name).includes(normalizedSearch) ||
        normalizeFilterValue(project.small_description).includes(normalizedSearch);

      return matchesSearch && matchesSelectedTags(project.tags, selectedTags);
    });
  }, [projects, searchQuery, selectedTags]);

  if (loading) {
    return (
      <div className="py-20 text-center">
        <div className="inline-block h-12 w-12 animate-spin rounded-full border-b-2 border-primary"></div>
        <p className="mt-4 text-muted-foreground">Загрузка проектов...</p>
      </div>
    );
  }

  return (
    <div className="py-12">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="mb-4 text-3xl font-bold text-foreground md:text-4xl">Все проекты</h1>
            <p className="text-lg text-muted-foreground">Фильтры синхронизированы с API: поиск по названию и поиск по тегам</p>
          </div>
          <button
            onClick={() => navigate('/projects/create')}
            className="inline-flex items-center space-x-2 whitespace-nowrap rounded-xl bg-primary px-6 py-3 text-white transition-colors hover:bg-accent"
          >
            <Plus className="h-5 w-5" />
            <span>Создать проект</span>
          </button>
        </div>

        <div className="mb-8 space-y-4">
          <div className="rounded-2xl border border-border bg-white p-5 shadow-sm">
            <label className="mb-3 block text-sm font-semibold text-foreground">Поиск по названию проекта</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                placeholder="Введите название проекта..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="app-input w-full pl-10 pr-4"
              />
            </div>
          </div>

          <TagSearchFilter
            title="Поиск по тегам"
            subtitle="Теги передаются в API как повторяющийся параметр tags и дополнительно проверяются без учёта регистра."
            placeholder="Например: python, backend, ai"
            selectedTags={selectedTags}
            onChange={setSelectedTags}
            availableTags={allTags}
          />
        </div>

        <div className="mb-6 text-muted-foreground">Найдено проектов: {filteredProjects.length}</div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filteredProjects.map((project) => (
            <Link
              key={project.id}
              to={`/projects/${project.id}`}
              className="group overflow-hidden rounded-2xl border border-border bg-white shadow-sm transition-all hover:-translate-y-1 hover:shadow-lg"
            >
              <div className="aspect-video overflow-hidden bg-muted">
                <ImageWithFallback
                  src={project.image}
                  alt={project.name}
                  className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                />
              </div>
              <div className="p-6">
                <h3 className="mb-2 text-xl font-semibold transition-colors group-hover:text-primary">{project.name}</h3>
                <p className="mb-4 line-clamp-2 text-sm text-muted-foreground">{project.small_description}</p>
                <div className="mb-4 flex flex-wrap gap-2">
                  {project.tags.slice(0, 4).map((tag) => (
                    <span key={tag} className="rounded-full bg-secondary px-3 py-1 text-xs text-secondary-foreground">
                      {tag}
                    </span>
                  ))}
                </div>
                <div className="flex items-center justify-between text-sm text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Users className="h-4 w-4" />
                    <span>{project.memberships.length} участников</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    <span>{new Date(project.created_at).toLocaleDateString('ru-RU')}</span>
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>

        {filteredProjects.length === 0 && (
          <div className="mt-8 rounded-2xl border border-border bg-white px-6 py-12 text-center shadow-sm">
            <h3 className="mb-2 text-xl font-semibold">Ничего не найдено</h3>
            <p className="text-muted-foreground">Попробуйте изменить название проекта или набор тегов.</p>
          </div>
        )}
      </div>
    </div>
  );
}
