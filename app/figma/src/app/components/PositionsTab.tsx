import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { Loader2, Briefcase, MapPin, Clock, Search, Filter } from 'lucide-react';
import { usePositionsQuery } from '../../api/hooks/usePositions';
import type { PositionListParams, PositionLocationType, PositionLoad } from '../../api/types';

const LOCATION_TYPES: { value: PositionLocationType; label: string; icon: string }[] = [
  { value: 'remote', label: 'Удаленно', icon: '🌍' },
  { value: 'onsite', label: 'В офисе', icon: '🏢' },
  { value: 'hybrid', label: 'Гибрид', icon: '🔄' },
];

const LOAD_TYPES: { value: PositionLoad; label: string; color: string }[] = [
  { value: 'low', label: 'Низкая', color: 'text-green-600' },
  { value: 'medium', label: 'Средняя', color: 'text-yellow-600' },
  { value: 'high', label: 'Высокая', color: 'text-red-600' },
];

export function PositionsTab() {
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<PositionListParams>({
    page: 1,
    page_size: 10,
  });

  const { data: positionsData, isLoading } = usePositionsQuery(filters);
  const positions = positionsData?.items || [];

  const handleFilterChange = (key: keyof PositionListParams, value: any) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value || undefined,
      page: 1, // Reset to first page when filters change
    }));
  };

  const handleResetFilters = () => {
    setFilters({
      page: 1,
      page_size: 10,
    });
  };

  const getLocationType = (type: string) => {
    return LOCATION_TYPES.find((t) => t.value === type) || { value: type as PositionLocationType, label: type, icon: '📍' };
  };

  const getLoadType = (load: string) => {
    return LOAD_TYPES.find((l) => l.value === load) || { value: load as PositionLoad, label: load, color: 'text-gray-600' };
  };

  const hasActiveFilters = filters.title || filters.location_type || filters.expected_load || filters.is_open !== undefined;

  return (
    <div className="space-y-6">
      {/* Filters */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Search className="w-5 h-5" />
              <CardTitle className="text-lg">Поиск позиций</CardTitle>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
            >
              <Filter className="w-4 h-4 mr-2" />
              {showFilters ? 'Скрыть фильтры' : 'Показать фильтры'}
            </Button>
          </div>
        </CardHeader>
        {showFilters && (
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="title">Название позиции</Label>
                <Input
                  id="title"
                  placeholder="Поиск по названию..."
                  value={filters.title || ''}
                  onChange={(e) => handleFilterChange('title', e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="locationType">Тип локации</Label>
                <Select
                  value={filters.location_type || ''}
                  onValueChange={(value) => handleFilterChange('location_type', value as PositionLocationType)}
                >
                  <SelectTrigger id="locationType">
                    <SelectValue placeholder="Все типы" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Все типы</SelectItem>
                    {LOCATION_TYPES.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        <span className="mr-2">{type.icon}</span>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="expectedLoad">Ожидаемая нагрузка</Label>
                <Select
                  value={filters.expected_load || ''}
                  onValueChange={(value) => handleFilterChange('expected_load', value as PositionLoad)}
                >
                  <SelectTrigger id="expectedLoad">
                    <SelectValue placeholder="Любая нагрузка" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Любая нагрузка</SelectItem>
                    {LOAD_TYPES.map((load) => (
                      <SelectItem key={load.value} value={load.value}>
                        {load.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="isOpen">Статус</Label>
                <Select
                  value={filters.is_open === undefined ? '' : filters.is_open.toString()}
                  onValueChange={(value) => 
                    handleFilterChange('is_open', value === '' ? undefined : value === 'true')
                  }
                >
                  <SelectTrigger id="isOpen">
                    <SelectValue placeholder="Все позиции" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Все позиции</SelectItem>
                    <SelectItem value="true">Только открытые</SelectItem>
                    <SelectItem value="false">Только закрытые</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {hasActiveFilters && (
              <div className="flex justify-end">
                <Button variant="outline" size="sm" onClick={handleResetFilters}>
                  Сбросить фильтры
                </Button>
              </div>
            )}
          </CardContent>
        )}
      </Card>

      {/* Results */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      ) : positions.length > 0 ? (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Найдено позиций: {positionsData?.total || 0}
            </p>
          </div>

          <div className="grid gap-4">
            {positions.map((position) => {
              const locationType = getLocationType(position.location_type);
              const loadType = getLoadType(position.expected_load);

              return (
                <Card key={position.id} className="hover:shadow-md transition-shadow">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-lg mb-2">{position.title}</CardTitle>
                        <div className="flex flex-wrap gap-2 mb-3">
                          <Badge variant={position.is_open ? 'default' : 'secondary'}>
                            {position.is_open ? 'Открыта' : 'Закрыта'}
                          </Badge>
                          <Badge variant="outline" className="gap-1">
                            <MapPin className="w-3 h-3" />
                            {locationType.icon} {locationType.label}
                          </Badge>
                          <Badge variant="outline" className={`gap-1 ${loadType.color}`}>
                            <Clock className="w-3 h-3" />
                            {loadType.label}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <p className="text-sm text-muted-foreground">{position.description}</p>

                    {position.required_skills && position.required_skills.length > 0 && (
                      <div>
                        <p className="text-xs font-medium mb-2">Требуемые навыки:</p>
                        <div className="flex flex-wrap gap-2">
                          {position.required_skills.map((skill, index) => (
                            <Badge key={index} variant="secondary">
                              {skill}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {position.responsibilities && (
                      <div>
                        <p className="text-xs font-medium mb-1">Обязанности:</p>
                        <p className="text-sm text-muted-foreground">{position.responsibilities}</p>
                      </div>
                    )}

                    <div className="flex justify-end pt-2">
                      <Button size="sm" disabled={!position.is_open}>
                        Откликнуться
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {/* Pagination */}
          {positionsData && positionsData.total > filters.page_size! && (
            <div className="flex justify-center gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={filters.page === 1}
                onClick={() => handleFilterChange('page', (filters.page || 1) - 1)}
              >
                Назад
              </Button>
              <span className="flex items-center px-4 text-sm">
                Страница {filters.page} из {Math.ceil(positionsData.total / filters.page_size!)}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={filters.page! >= Math.ceil(positionsData.total / filters.page_size!)}
                onClick={() => handleFilterChange('page', (filters.page || 1) + 1)}
              >
                Вперед
              </Button>
            </div>
          )}
        </div>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Briefcase className="w-12 h-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground mb-2">
              {hasActiveFilters ? 'Позиции не найдены' : 'Пока нет доступных позиций'}
            </p>
            {hasActiveFilters && (
              <Button variant="outline" size="sm" onClick={handleResetFilters}>
                Сбросить фильтры
              </Button>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
