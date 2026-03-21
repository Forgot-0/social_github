import { useState } from 'react';
import { useNavigate } from 'react-router';
import { ProjectCard } from '../components/ProjectCard';
import { StatsCard } from '../components/StatsCard';
import { EmptyState } from '../components/EmptyState';
import { HeroBanner } from '../components/HeroBanner';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { Label } from '../components/ui/label';
import { Search, Filter, Briefcase, Users, TrendingUp, Sparkles, Loader2, Plus, X } from 'lucide-react';
import { useProjectsQuery, usePositionsQuery } from '../../api/hooks';
import { useAuth } from '../contexts/AuthContext';
import { COMMON_SKILLS } from '../constants/skills';

export function HomePage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [customSkillInput, setCustomSkillInput] = useState('');
  const [showAllSkills, setShowAllSkills] = useState(false);

  const { data: projectsData, isLoading } = useProjectsQuery({
    name: searchQuery || undefined,
    tags: selectedTags.length > 0 ? selectedTags : undefined,
    page: 1,
    page_size: 20,
  });

  const { data: allProjectsData } = useProjectsQuery({
    page: 1,
    page_size: 100,
  });

  const { data: positionsData } = usePositionsQuery({
    is_open: true,
    page: 1,
    page_size: 100,
  });

  const { data: newProjectsData } = useProjectsQuery({
    name: searchQuery || undefined,
    tags: selectedTags.length > 0 ? selectedTags : undefined,
    page: 1,
    page_size: 20,
    sort: '-created_at',
  });

  const toggleTag = (tag: string) => {
    setSelectedTags(prev =>
      prev.includes(tag)
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    );
  };

  const handleAddCustomSkill = () => {
    const trimmedSkill = customSkillInput.trim();
    if (!trimmedSkill) return;
    if (selectedTags.includes(trimmedSkill)) {
      setCustomSkillInput('');
      return;
    }
    setSelectedTags(prev => [...prev, trimmedSkill]);
    setCustomSkillInput('');
  };

  const projects = projectsData?.items || [];
  const newProjects = newProjectsData?.items || [];
  const totalProjects = allProjectsData?.total || projectsData?.total || 0;
  const totalPositions = positionsData?.total || 0;

  const displayedSkills = showAllSkills ? COMMON_SKILLS : COMMON_SKILLS.slice(0, 12);

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Hero Banner или приветствие */}
      {!user ? (
        <HeroBanner />
      ) : (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-6 mb-8 border border-blue-100">
          <h2 className="text-2xl font-bold mb-2">Привет, {user.username}! Найдите новый проект.</h2>
          <p className="text-muted-foreground">Исследуйте актуальные проекты и находите идеальные возможности для сотрудничества.</p>
        </div>
      )}

      {/* Статистика */}
      <div className="grid gap-4 md:grid-cols-4 mb-8">
        <StatsCard
          title="Активных проектов"
          value={totalProjects}
          icon={Briefcase}
          trend={{ value: 12, isPositive: true }}
        />
        <StatsCard
          title="Открытых вакансий"
          value={totalPositions}
          icon={TrendingUp}
          trend={{ value: 8, isPositive: true }}
        />
        <StatsCard
          title="Участников"
          value="—"
          icon={Users}
          description="Скоро доступно"
        />
        <StatsCard
          title="Успешных матчей"
          value="—"
          icon={Sparkles}
          description="Скоро доступно"
        />
      </div>

      <div className="mb-6 space-y-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-5 h-5" />
          <Input
            placeholder="Поиск проектов..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-muted-foreground" />
            <Label className="text-sm text-muted-foreground">Фильтр по навыкам:</Label>
          </div>

          {/* Выбранные навыки */}
          {selectedTags.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {selectedTags.map((tag) => (
                <Badge
                  key={tag}
                  variant="default"
                  className="gap-1 pl-3 pr-2"
                >
                  {tag}
                  <button
                    onClick={() => toggleTag(tag)}
                    className="ml-1 hover:text-red-300"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </Badge>
              ))}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedTags([])}
                className="text-xs h-7"
              >
                Сбросить все
              </Button>
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
                .filter(skill => !selectedTags.includes(skill))
                .map((tag) => (
                  <Badge
                    key={tag}
                    variant="outline"
                    className="cursor-pointer hover:bg-accent"
                    onClick={() => toggleTag(tag)}
                  >
                    <Plus className="w-3 h-3 mr-1" />
                    {tag}
                  </Badge>
                ))}
              {!showAllSkills && COMMON_SKILLS.length > 12 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowAllSkills(true)}
                  className="text-xs h-7"
                >
                  Показать все
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>

      <Tabs defaultValue="all" className="mb-6">
        <TabsList>
          <TabsTrigger value="all">Все проекты</TabsTrigger>
          <TabsTrigger value="recommended">Рекомендации</TabsTrigger>
          <TabsTrigger value="new">Новые</TabsTrigger>
        </TabsList>
        
        <TabsContent value="all" className="mt-6">
          {isLoading ? (
            <div className="flex justify-center">
              <Loader2 className="animate-spin h-6 w-6 text-gray-500" />
            </div>
          ) : projects.length > 0 ? (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-2">
              {projects.map((project) => (
                <ProjectCard key={project.id} project={project} />
              ))}
            </div>
          ) : (
            <EmptyState
              icon={Search}
              title="Проекты не найдены"
              description="Попробуйте изменить критерии поиска или сбросить фильтры"
              action={{
                label: 'Сбросить фильтры',
                onClick: () => {
                  setSearchQuery('');
                  setSelectedTags([]);
                },
              }}
            />
          )}
        </TabsContent>

        <TabsContent value="recommended" className="mt-6">
          <EmptyState
            icon={Sparkles}
            title="Рекомендации скоро появятся"
            description="Заполните профиль и навыки для персональных рекомендаций проектов"
            action={{
              label: 'Перейти к настройкам',
              onClick: () => navigate('/settings'),
            }}
          />
        </TabsContent>

        <TabsContent value="new" className="mt-6">
          {isLoading ? (
            <div className="flex justify-center">
              <Loader2 className="animate-spin h-6 w-6 text-gray-500" />
            </div>
          ) : newProjects.length > 0 ? (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-2">
              {newProjects.map((project) => (
                <ProjectCard key={project.id} project={project} />
              ))}
            </div>
          ) : (
            <EmptyState
              icon={Search}
              title="Новые проекты не найдены"
              description="Попробуйте изменить критерии поиска"
            />
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}