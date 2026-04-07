import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { FolderOpen, Plus, Search, Users, Calendar } from 'lucide-react';
import { api } from '../lib/api';
import { toast } from 'sonner';
import { TagSearchFilter, normalizeFilterValue } from '../components/TagSearchFilter';
import { ImageWithFallback } from '../components/figma/ImageWithFallback';

interface Project {
  id: number;
  owner_id: number;
  name: string;
  small_description: string;
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
      <text x="600" y="320" text-anchor="middle" font-family="Arial, sans-serif" font-size="56" fill="#334155">ИнКоллаб</text>
      <text x="600" y="390" text-anchor="middle" font-family="Arial, sans-serif" font-size="28" fill="#64748b">My projects</text>
    </svg>
  `);

function normalizeProject(project: any): Project {
  return {
    ...project,
    small_description: project?.small_description || '',
    tags: Array.isArray(project?.tags) ? project.tags : [],
    memberships: Array.isArray(project?.memberships) ? project.memberships : [],
    image: project?.image || project?.meta_data?.image || project?.meta_data?.cover_image || DEFAULT_PROJECT_IMAGE,
  };
}

function matchesSelectedTags(projectTags: string[], selectedTags: string[]) {
  if (selectedTags.length === 0) return true;
  const normalizedProjectTags = projectTags.map((tag) => normalizeFilterValue(tag));
  return selectedTags.every((tag) => normalizedProjectTags.includes(normalizeFilterValue(tag)));
}

export function MyProjects() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      void loadProjects();
    }, 250);

    return () => window.clearTimeout(timeout);
  }, [searchQuery, selectedTags]);

  const loadProjects = async () => {
    try {
      setLoading(true);

      const [myProjectsResponse, filteredProjectsResponse] = await Promise.all([
        api.getMyProjects({ page: 1, page_size: 100 }),
        api.getProjects({
          page: 1,
          page_size: 100,
          sort: 'created_at:desc',
          name: searchQuery.trim() || undefined,
          tags: selectedTags.length ? selectedTags : undefined,
        }),
      ]);

      const myProjectIds = new Set(
        Array.isArray(myProjectsResponse?.items) ? myProjectsResponse.items.map((project: any) => project.id) : []
      );
      const filteredProjects = Array.isArray(filteredProjectsResponse?.items) ? filteredProjectsResponse.items : [];

      setProjects(filteredProjects.filter((project: any) => myProjectIds.has(project.id)).map(normalizeProject));
    } catch (error: any) {
      console.error('Failed to load my projects:', error);
      toast.error(error?.error?.message || 'Не удалось загрузить ваши проекты');
      setProjects([]);
    } finally {
      setLoading(false);
    }
  };

  const allTags = useMemo(
    () => Array.from(new Set(projects.flatMap((project) => project.tags))).sort((a, b) => a.localeCompare(b)),
    [projects]
  );

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
        <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="mb-4 text-3xl font-bold text-foreground md:text-4xl">Мои проекты</h1>
            <p className="text-lg text-muted-foreground">Фильтрация строится по новой схеме API: список ваших проектов + фильтры каталога по name и tags</p>
          </div>
          <Link to="/projects/create" className="inline-flex items-center gap-2 rounded-xl bg-primary px-6 py-3 text-white transition-colors hover:bg-accent">
            <Plus className="h-5 w-5" />
            <span>Новый проект</span>
          </Link>
        </div>

        <div className="mb-8 space-y-4">
          <div className="rounded-2xl border border-border bg-white p-5 shadow-sm">
            <label className="mb-3 block text-sm font-semibold text-foreground">Поиск по моим проектам</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="По названию проекта..."
                className="app-input w-full pl-10 pr-4"
              />
            </div>
          </div>

          <TagSearchFilter
            title="Теги проектов"
            subtitle="Теги передаются в API каталога повторяющимся параметром tags, а затем остаются только ваши проекты."
            placeholder="Например: go, typescript, ml"
            selectedTags={selectedTags}
            onChange={setSelectedTags}
            availableTags={allTags}
          />
        </div>

        {filteredProjects.length === 0 ? (
          <div className="rounded-2xl border border-border bg-white py-12 text-center shadow-sm">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-muted">
              <FolderOpen className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="mb-2 text-xl font-semibold">Проекты не найдены</h3>
            <p className="mb-4 text-muted-foreground">Попробуйте изменить фильтры или создайте новый проект.</p>
            <Link to="/projects/create" className="inline-flex rounded-xl bg-primary px-6 py-3 text-white transition-colors hover:bg-accent">
              Создать проект
            </Link>
          </div>
        ) : (
          <div className="grid gap-6 lg:grid-cols-2 xl:grid-cols-3">
            {filteredProjects.map((project) => (
              <Link key={project.id} to={`/projects/${project.id}`} className="group overflow-hidden rounded-3xl border border-border bg-white shadow-sm transition-all hover:-translate-y-1 hover:shadow-lg">
                <div className="aspect-[16/9] overflow-hidden bg-muted">
                  <ImageWithFallback src={project.image} alt={project.name} className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105" />
                </div>
                <div className="p-6">
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <h3 className="text-xl font-semibold transition-colors group-hover:text-primary">{project.name}</h3>
                    <span className="rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary">Мой проект</span>
                  </div>
                  <p className="mb-4 line-clamp-2 text-sm text-muted-foreground">{project.small_description}</p>
                  <div className="mb-5 flex flex-wrap gap-2">
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
        )}
      </div>
    </div>
  );
}
