import { useState } from 'react';
import { Link } from 'react-router';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { PlusCircle, Briefcase, Users, Settings, CheckCircle2, XCircle, Clock, Loader2 } from 'lucide-react';
import { useMyProjectsQuery, useMyApplicationsQuery } from '../../api/hooks';
import { usePositionsQuery, useProjectsQuery } from '../../api/hooks';
import { formatDistanceToNow } from 'date-fns';
import { ru } from 'date-fns/locale';

export function MyProjectsPage() {
  const { data: myProjectsData, isLoading: projectsLoading } = useMyProjectsQuery();
  const { data: applicationsData, isLoading: applicationsLoading } = useMyApplicationsQuery();
  const { data: positionsData, isLoading: positionsLoading } = usePositionsQuery();
  const { data: projectsData, isLoading: projectsDataLoading } = useProjectsQuery();

  const myProjects = myProjectsData?.items || [];
  const myApplications = applicationsData?.items || [];
  const positions = positionsData?.items || [];
  const projects = projectsData?.items || [];

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">Мои проекты</h1>
          <p className="text-muted-foreground">
            Управляйте своими проектами и отслеживайте участие
          </p>
        </div>
        <Link to="/create-project">
          <Button className="gap-2">
            <PlusCircle className="w-4 h-4" />
            Создать проект
          </Button>
        </Link>
      </div>

      <Tabs defaultValue="owned" className="space-y-6">
        <TabsList>
          <TabsTrigger value="owned">Мои проекты ({myProjects.length})</TabsTrigger>
          <TabsTrigger value="applications">Мои отклики ({myApplications.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="owned" className="space-y-4">
          {projectsLoading ? (
            <div className="flex justify-center">
              <Loader2 className="animate-spin h-6 w-6 text-gray-500" />
            </div>
          ) : myProjects.length > 0 ? (
            myProjects.map((project) => (
              <Card key={project.id}>
                <CardHeader>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <CardTitle className="text-xl">
                        <Link to={`/projects/${project.id}`} className="hover:text-blue-600">
                          {project.name}
                        </Link>
                      </CardTitle>
                      <CardDescription className="mt-2 line-clamp-2">
                        {project.small_description}
                      </CardDescription>
                    </div>
                    <Badge variant="default">
                      {project.visibility}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-6 text-sm text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <Users className="w-4 h-4" />
                        <span>{project.memberships?.length || 0} участников</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        <span>{project.updated_at ? formatDistanceToNow(new Date(project.updated_at), { addSuffix: true, locale: ru }) : ''}</span>
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <Link to={`/projects/${project.id}`}>
                        <Button variant="outline" size="sm">
                          Подробнее
                        </Button>
                      </Link>
                      <Button variant="ghost" size="sm">
                        <Settings className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Briefcase className="w-12 h-12 text-muted-foreground mb-4" />
                <p className="text-muted-foreground mb-4">У вас пока нет созданных проектов</p>
                <Link to="/create-project">
                  <Button>Создать первый проект</Button>
                </Link>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="applications" className="space-y-4">
          {applicationsLoading || positionsLoading || projectsDataLoading ? (
            <div className="flex justify-center">
              <Loader2 className="animate-spin h-6 w-6 text-gray-500" />
            </div>
          ) : myApplications.length > 0 ? (
            myApplications.map((application) => {
              const position = positions.find(pos => pos.id === application.position_id);
              const project = projects.find(p => p.id === application.project_id);

              if (!position || !project) return null;

              return (
                <Card key={application.id}>
                  <CardHeader>
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <CardTitle className="text-lg">{position.title}</CardTitle>
                        <CardDescription className="mt-1">
                          в проекте "{project.name}"
                        </CardDescription>
                      </div>
                      <Badge
                        variant={
                          application.status === 'accepted'
                            ? 'default'
                            : application.status === 'rejected'
                            ? 'destructive'
                            : 'secondary'
                        }
                        className="gap-1"
                      >
                        {application.status === 'accepted' && <CheckCircle2 className="w-3 h-3" />}
                        {application.status === 'rejected' && <XCircle className="w-3 h-3" />}
                        {application.status === 'pending' && <Clock className="w-3 h-3" />}
                        {application.status === 'accepted'
                          ? 'Принят'
                          : application.status === 'rejected'
                          ? 'Отклонен'
                          : 'На рассмотрении'}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {application.message && (
                        <div className="text-sm">
                          <span className="text-muted-foreground">Сообщение: </span>
                          {application.message}
                        </div>
                      )}
                      <div className="flex items-center justify-between text-sm text-muted-foreground">
                        <span>
                          Отправлено {application.created_at ? formatDistanceToNow(new Date(application.created_at), { addSuffix: true, locale: ru }) : 'недавно'}
                        </span>
                        <Link to={`/projects/${project.id}`}>
                          <Button variant="outline" size="sm">
                            Перейти к проекту
                          </Button>
                        </Link>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Briefcase className="w-12 h-12 text-muted-foreground mb-4" />
                <p className="text-muted-foreground mb-4">У вас пока нет откликов</p>
                <Link to="/">
                  <Button>Найти вакансии</Button>
                </Link>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}