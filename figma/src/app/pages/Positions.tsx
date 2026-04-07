import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, MapPin, Clock, Send, Briefcase } from 'lucide-react';
import { api } from '../lib/api';
import { toast } from 'sonner';
import { useAuth } from '../contexts/AuthContext';
import { TagSearchFilter, normalizeFilterValue } from '../components/TagSearchFilter';
import { StyledSelect } from '../components/StyledSelect';

interface Position {
  id: string;
  project_id: number;
  title: string;
  description: string;
  responsibilities?: string;
  required_skills: string[];
  is_open: boolean;
  location_type: 'remote' | 'onsite' | 'hybrid';
  expected_load: 'low' | 'medium' | 'high';
  project_name?: string;
}

const locationTypes: Record<Position['location_type'], string> = {
  remote: 'Удаленно',
  hybrid: 'Гибрид',
  onsite: 'Офис',
};

const loadTypes: Record<Position['expected_load'], string> = {
  low: 'Низкая',
  medium: 'Средняя',
  high: 'Высокая',
};

function normalizePosition(position: any): Position {
  return {
    ...position,
    description: position?.description || '',
    required_skills: Array.isArray(position?.required_skills) ? position.required_skills : [],
    project_name: position?.project_name || position?.project?.name || `Проект #${position?.project_id}`,
  };
}

function matchesSelectedSkills(positionSkills: string[], selectedSkills: string[]) {
  if (selectedSkills.length === 0) return true;
  const normalizedPositionSkills = positionSkills.map((skill) => normalizeFilterValue(skill));
  return selectedSkills.every((skill) => normalizedPositionSkills.includes(normalizeFilterValue(skill)));
}

export function Positions() {
  const { user } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [locationFilter, setLocationFilter] = useState<string>('all');
  const [loadFilter, setLoadFilter] = useState<string>('all');
  const [skillFilter, setSkillFilter] = useState<string[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(true);

  const allSkills = useMemo(
    () => Array.from(new Set(positions.flatMap((position) => position.required_skills))).sort((a, b) => a.localeCompare(b)),
    [positions]
  );

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      void loadPositions();
    }, 250);

    return () => window.clearTimeout(timeout);
  }, [searchQuery, locationFilter, loadFilter, skillFilter]);

  const loadPositions = async () => {
    try {
      setLoading(true);
      const data = await api.getPositions({
        page: 1,
        page_size: 100,
        sort: 'title:asc',
        is_open: true,
        title: searchQuery.trim() || undefined,
        location_type: locationFilter !== 'all' ? locationFilter : undefined,
        expected_load: loadFilter !== 'all' ? loadFilter : undefined,
        required_skills: skillFilter.length ? skillFilter : undefined,
      });
      const items = Array.isArray(data?.items) ? data.items : [];
      setPositions(items.map(normalizePosition));
    } catch (error: any) {
      console.error('Failed to load positions:', error);
      toast.error(error?.error?.message || 'Не удалось загрузить позиции из API');
      setPositions([]);
    } finally {
      setLoading(false);
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

  const filteredPositions = useMemo(() => {
    const normalizedSearch = normalizeFilterValue(searchQuery);

    return positions.filter((position) => {
      const matchesSearch =
        !normalizedSearch ||
        normalizeFilterValue(position.title).includes(normalizedSearch) ||
        normalizeFilterValue(position.project_name || '').includes(normalizedSearch) ||
        position.required_skills.some((skill) => normalizeFilterValue(skill).includes(normalizedSearch));

      const matchesLocation = locationFilter === 'all' || normalizeFilterValue(position.location_type) === normalizeFilterValue(locationFilter);
      const matchesLoad = loadFilter === 'all' || normalizeFilterValue(position.expected_load) === normalizeFilterValue(loadFilter);
      const matchesSkills = matchesSelectedSkills(position.required_skills, skillFilter);

      return matchesSearch && matchesLocation && matchesLoad && matchesSkills && position.is_open;
    });
  }, [positions, searchQuery, locationFilter, loadFilter, skillFilter]);

  const clearFilters = () => {
    setSearchQuery('');
    setLocationFilter('all');
    setLoadFilter('all');
    setSkillFilter([]);
  };

  const hasActiveFilters =
    searchQuery.trim().length > 0 || locationFilter !== 'all' || loadFilter !== 'all' || skillFilter.length > 0;

  if (loading) {
    return (
      <div className="py-20 text-center">
        <div className="inline-block h-12 w-12 animate-spin rounded-full border-b-2 border-primary"></div>
        <p className="mt-4 text-muted-foreground">Загрузка позиций...</p>
      </div>
    );
  }

  return (
    <div className="py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="mb-4 text-3xl font-bold text-foreground md:text-4xl">Открытые позиции</h1>
          <p className="text-lg text-muted-foreground">Фильтры передаются в API: title, location_type, expected_load и required_skills</p>
        </div>

        <div className="mb-8 space-y-4">
          <div className="rounded-2xl border border-border bg-white p-6 shadow-sm">
            <div className="grid gap-4 lg:grid-cols-[minmax(0,1.7fr)_minmax(200px,0.7fr)_minmax(200px,0.7fr)]">
              <div>
                <label className="mb-2 block text-sm font-semibold text-foreground">Поиск по позициям</label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
                  <input
                    type="text"
                    placeholder="По названию позиции..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
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

            {hasActiveFilters ? (
              <div className="mt-4 flex justify-end">
                <button onClick={clearFilters} className="text-sm font-medium text-primary hover:underline">
                  Сбросить фильтры
                </button>
              </div>
            ) : null}
          </div>

          <TagSearchFilter
            title="Фильтр по навыкам"
            subtitle="Выбранные навыки отправляются в API параметром required_skills и дополнительно проверяются без учёта регистра."
            placeholder="Например: python, react, ml"
            selectedTags={skillFilter}
            onChange={setSkillFilter}
            availableTags={allSkills}
          />
        </div>

        <div className="mb-6 text-muted-foreground">Найдено позиций: {filteredPositions.length}</div>

        <div className="space-y-4">
          {filteredPositions.map((position) => (
            <div key={position.id} className="rounded-2xl border border-border bg-white p-6 shadow-sm transition-shadow hover:shadow-md">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div className="flex-1">
                  <div className="mb-2">
                    <h3 className="text-xl font-semibold mb-1">{position.title}</h3>
                    <Link to={`/projects/${position.project_id}`} className="text-primary hover:underline text-sm">
                      {position.project_name}
                    </Link>
                  </div>
                  <p className="mb-4 text-muted-foreground">{position.description}</p>
                  <div className="mb-4 flex flex-wrap gap-2">
                    {position.required_skills.map((skill) => (
                      <span key={skill} className="rounded-full bg-secondary px-3 py-1 text-sm text-secondary-foreground">
                        {skill}
                      </span>
                    ))}
                  </div>
                  <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
                    <div className="flex items-center space-x-1">
                      <MapPin className="w-4 h-4" />
                      <span>{locationTypes[position.location_type]}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Clock className="w-4 h-4" />
                      <span>{loadTypes[position.expected_load]}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Briefcase className="w-4 h-4" />
                      <span>{position.is_open ? 'Открыта' : 'Закрыта'}</span>
                    </div>
                  </div>
                </div>
                <div className="flex-shrink-0">
                  <button
                    onClick={() => handleApply(position.id)}
                    className="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-3 text-white transition-colors hover:bg-accent"
                  >
                    <Send className="h-4 w-4" />
                    <span>Откликнуться</span>
                  </button>
                </div>
              </div>
            </div>
          ))}

          {filteredPositions.length === 0 && (
            <div className="rounded-2xl border border-border bg-white px-6 py-12 text-center shadow-sm">
              <h3 className="mb-2 text-xl font-semibold">Подходящие позиции не найдены</h3>
              <p className="text-muted-foreground">Попробуйте изменить фильтры или очистить выбранные навыки.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}