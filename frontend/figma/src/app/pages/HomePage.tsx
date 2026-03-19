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
import { Search, Filter, Briefcase, Users, TrendingUp, Sparkles, Loader2 } from 'lucide-react';
import { useProjectsQuery } from '../../api/hooks';

export function HomePage() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);

  const { data: projectsData, isLoading } = useProjectsQuery({
    name: searchQuery || undefined,
    tags: selectedTags.length > 0 ? selectedTags : undefined,
    page: 1,
    page_size: 20,
  });

  const toggleTag = (tag: string) => {
    setSelectedTags(prev =>
      prev.includes(tag)
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    );
  };

  const projects = projectsData?.items || [];
  const totalPositions = projects.reduce((acc, p) => acc + (p.memberships?.length || 0), 0);

  const popularTags = ['React', 'TypeScript', 'Python', 'Design', 'Mobile', 'Backend', 'Frontend', 'Стартап'];

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Hero Banner */}
      <HeroBanner />

      {/* Статистика */}
      <div className="grid gap-4 md:grid-cols-4 mb-8">
        <StatsCard
          title="Активных проектов"
          value={projectsData?.total || 0}
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
          value="150+"
          icon={Users}
          description="Активных пользователей"
        />
        <StatsCard
          title="Успешных матчей"
          value="45"
          icon={Sparkles}
          description="За этот месяц"
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

        <div className="flex items-center gap-2 flex-wrap">
          <Filter className="w-4 h-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">Фильтр по навыкам:</span>
          {popularTags.map((tag) => (
            <Badge
              key={tag}
              variant={selectedTags.includes(tag) ? 'default' : 'outline'}
              className="cursor-pointer"
              onClick={() => toggleTag(tag)}
            >
              {tag}
            </Badge>
          ))}
          {selectedTags.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedTags([])}
              className="text-xs"
            >
              Сбросить
            </Button>
          )}
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
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-2">
            {projects.slice(0, 2).map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
          <div className="text-center py-8 text-sm text-muted-foreground">
            Рекомендации основаны на ваших навыках: React, TypeScript, Node.js
          </div>
        </TabsContent>

        <TabsContent value="new" className="mt-6">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-2">
            {[...projects].reverse().map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}