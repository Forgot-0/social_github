import { useState } from 'react';
import { Link } from 'react-router';
import { useQuery } from '@tanstack/react-query';
import { positionsApi } from '../../api/client';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { EmptyState } from '../components/EmptyState';
import { ProjectCardSkeleton } from '../components/ProjectCardSkeleton';
import { ChevronLeft, ChevronRight, Briefcase, MapPin, Clock, ExternalLink, Plus, X } from 'lucide-react';
import type { PositionDTO } from '../../api/types';
import { COMMON_SKILLS } from '../constants/skills';

export function PositionsPage() {
  const [search, setSearch] = useState('');
  const [locationType, setLocationType] = useState<string | undefined>();
  const [expectedLoad, setExpectedLoad] = useState<string | undefined>();
  const [onlyOpen, setOnlyOpen] = useState(true);
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);
  const [customSkillInput, setCustomSkillInput] = useState('');
  const [showAllSkills, setShowAllSkills] = useState(false);
  const [page, setPage] = useState(1);
  const pageSize = 12;

  const { data: positionsData, isLoading } = useQuery({
    queryKey: ['positions', { search, locationType, expectedLoad, onlyOpen, selectedSkills, page, pageSize }],
    queryFn: () =>
      positionsApi.getPositions({
        title: search || undefined,
        location_type: locationType as any,
        expected_load: expectedLoad as any,
        is_open: onlyOpen,
        required_skills: selectedSkills.length > 0 ? selectedSkills : undefined,
        page,
        page_size: pageSize,
      }),
  });

  const positions = positionsData?.items || [];
  const totalPages = positionsData ? Math.ceil(positionsData.total / pageSize) : 0;

  const handleResetFilters = () => {
    setSearch('');
    setLocationType(undefined);
    setExpectedLoad(undefined);
    setOnlyOpen(true);
    setSelectedSkills([]);
    setPage(1);
  };

  const toggleSkill = (skill: string) => {
    setSelectedSkills(prev =>
      prev.includes(skill)
        ? prev.filter(s => s !== skill)
        : [...prev, skill]
    );
    setPage(1);
  };

  const handleAddCustomSkill = () => {
    const trimmedSkill = customSkillInput.trim();
    if (!trimmedSkill) return;
    if (selectedSkills.includes(trimmedSkill)) {
      setCustomSkillInput('');
      return;
    }
    setSelectedSkills(prev => [...prev, trimmedSkill]);
    setCustomSkillInput('');
    setPage(1);
  };

  const displayedSkills = showAllSkills ? COMMON_SKILLS : COMMON_SKILLS.slice(0, 12);

  const getLocationTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      remote: 'Удалённо',
      onsite: 'В офисе',
      hybrid: 'Гибрид',
    };
    return labels[type] || type;
  };

  const getExpectedLoadLabel = (load: string) => {
    const labels: Record<string, string> = {
      low: 'Низкая',
      medium: 'Средняя',
      high: 'Высокая',
    };
    return labels[load] || load;
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Все вакансии</h1>
          <p className="text-muted-foreground">
            Найдите интересную позицию в проектах студентов и стартапов
          </p>
        </div>

        {/* Фильтры */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Фильтры</CardTitle>
            <CardDescription>Настройте параметры поиска вакансий</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
              <div className="space-y-2">
                <Label htmlFor="search">Поиск по названию</Label>
                <Input
                  id="search"
                  placeholder="Введите название позиции..."
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value);
                    setPage(1);
                  }}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="locationType">Тип занятости</Label>
                <Select
                  value={locationType || 'all'}
                  onValueChange={(value) => {
                    setLocationType(value === 'all' ? undefined : value);
                    setPage(1);
                  }}
                >
                  <SelectTrigger id="locationType">
                    <SelectValue placeholder="Все типы" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Все типы</SelectItem>
                    <SelectItem value="remote">Удалённо</SelectItem>
                    <SelectItem value="onsite">В офисе</SelectItem>
                    <SelectItem value="hybrid">Гибрид</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="expectedLoad">Нагрузка</Label>
                <Select
                  value={expectedLoad || 'all'}
                  onValueChange={(value) => {
                    setExpectedLoad(value === 'all' ? undefined : value);
                    setPage(1);
                  }}
                >
                  <SelectTrigger id="expectedLoad">
                    <SelectValue placeholder="Любая нагрузка" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Любая нагрузка</SelectItem>
                    <SelectItem value="low">Низкая</SelectItem>
                    <SelectItem value="medium">Средняя</SelectItem>
                    <SelectItem value="high">Высокая</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="onlyOpen">Статус</Label>
                <Select
                  value={onlyOpen ? 'open' : 'all'}
                  onValueChange={(value) => {
                    setOnlyOpen(value === 'open');
                    setPage(1);
                  }}
                >
                  <SelectTrigger id="onlyOpen">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="open">Только открытые</SelectItem>
                    <SelectItem value="all">Все вакансии</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Фильтр по навыкам */}
            <div className="space-y-3 pt-4 border-t">
              <Label>Фильтр по навыкам</Label>

              {/* Выбранные навыки */}
              {selectedSkills.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {selectedSkills.map((skill) => (
                    <Badge
                      key={skill}
                      variant="default"
                      className="gap-1 pl-3 pr-2"
                    >
                      {skill}
                      <button
                        onClick={() => toggleSkill(skill)}
                        className="ml-1 hover:text-red-300"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
              )}

              {/* Добавить свой навык */}
              <div className="flex gap-2">
                <Input
                  placeholder="Добавьте свой навык..."
                  value={customSkillInput}
                  onChange={(e) => setCustomSkillInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddCustomSkill();
                    }
                  }}
                />
                <Button onClick={handleAddCustomSkill} variant="outline" size="sm">
                  <Plus className="w-4 h-4 mr-1" />
                  Добавить
                </Button>
              </div>

              {/* Популярные навыки */}
              <div>
                <Label className="text-sm text-muted-foreground mb-2 block">Популярные навыки:</Label>
                <div className="flex flex-wrap gap-2">
                  {displayedSkills
                    .filter(skill => !selectedSkills.includes(skill))
                    .map((skill) => (
                      <Badge
                        key={skill}
                        variant="outline"
                        className="cursor-pointer hover:bg-accent"
                        onClick={() => toggleSkill(skill)}
                      >
                        <Plus className="w-3 h-3 mr-1" />
                        {skill}
                      </Badge>
                    ))}
                  {!showAllSkills && COMMON_SKILLS.length > 12 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowAllSkills(true)}
                      className="text-xs h-7"
                    >
                      Показать все навыки
                    </Button>
                  )}
                </div>
              </div>
            </div>

            <div className="mt-4 flex justify-between items-center">
              <p className="text-sm text-muted-foreground">
                {positionsData ? `Найдено вакансий: ${positionsData.total}` : 'Загрузка...'}
              </p>
              <Button variant="outline" size="sm" onClick={handleResetFilters}>
                Сбросить фильтры
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Список вакансий */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <ProjectCardSkeleton key={i} />
            ))}
          </div>
        ) : positions.length === 0 ? (
          <EmptyState
            icon={Briefcase}
            title="Вакансий не найдено"
            description="Попробуйте изменить фильтры или сбросить их"
            action={
              <Button onClick={handleResetFilters}>
                Сбросить фильтры
              </Button>
            }
          />
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
              {positions.map((position) => (
                <PositionCardItem key={position.id} position={position} />
              ))}
            </div>

            {/* Пагинация */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  <ChevronLeft className="w-4 h-4 mr-1" />
                  Назад
                </Button>
                <span className="text-sm text-muted-foreground px-4">
                  Страница {page} из {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                >
                  Вперёд
                  <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

interface PositionCardItemProps {
  position: PositionDTO;
}

function PositionCardItem({ position }: PositionCardItemProps) {
  const getLocationTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      remote: 'Удалённо',
      onsite: 'В офисе',
      hybrid: 'Гибрид',
    };
    return labels[type] || type;
  };

  const getExpectedLoadLabel = (load: string) => {
    const labels: Record<string, string> = {
      low: 'Низкая',
      medium: 'Средняя',
      high: 'Высокая',
    };
    return labels[load] || load;
  };

  return (
    <Card className="flex flex-col">
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <CardTitle className="text-lg">{position.title}</CardTitle>
            <CardDescription className="mt-2 line-clamp-2">
              {position.description}
            </CardDescription>
          </div>
          <Badge 
            variant={position.is_open ? 'default' : 'secondary'}
            className={position.is_open ? 'bg-green-500 hover:bg-green-600' : 'bg-red-500 hover:bg-red-600'}
          >
            {position.is_open ? 'Открыта' : 'Закрыта'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col justify-between">
        <div className="space-y-3 mb-4">
          {position.location_type && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <MapPin className="w-4 h-4" />
              <span>{getLocationTypeLabel(position.location_type)}</span>
            </div>
          )}
          {position.expected_load && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="w-4 h-4" />
              <span>Нагрузка: {getExpectedLoadLabel(position.expected_load)}</span>
            </div>
          )}
          {position.required_skills && position.required_skills.length > 0 && (
            <div>
              <div className="text-sm font-medium mb-2">Требуемые навыки:</div>
              <div className="flex flex-wrap gap-2">
                {position.required_skills.slice(0, 5).map((skill, idx) => (
                  <Badge key={idx} variant="outline" className="text-xs">
                    {skill}
                  </Badge>
                ))}
                {position.required_skills.length > 5 && (
                  <Badge variant="outline" className="text-xs">
                    +{position.required_skills.length - 5}
                  </Badge>
                )}
              </div>
            </div>
          )}
        </div>

        <div className="pt-3 border-t">
          <Link to={`/projects/${position.project_id}`}>
            <Button variant="outline" size="sm" className="w-full gap-2">
              Перейти к проекту
              <ExternalLink className="w-4 h-4" />
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}