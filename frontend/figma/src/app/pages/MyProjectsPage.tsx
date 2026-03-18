import { useState } from 'react';
import { Link } from 'react-router';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { PlusCircle, Briefcase, Users, Settings, CheckCircle2, XCircle, Clock } from 'lucide-react';
import { MOCK_PROJECTS, CURRENT_USER, MOCK_APPLICATIONS } from '../data/mockData';
import { formatDistanceToNow } from 'date-fns';
import { ru } from 'date-fns/locale';

export function MyProjectsPage() {
  const myProjects = MOCK_PROJECTS.filter(p => p.ownerId === CURRENT_USER.id);
  const participatingProjects = MOCK_PROJECTS.filter(p =>
    p.participants.some(part => part.userId === CURRENT_USER.id)
  );

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
          <TabsTrigger value="participating">Участвую ({participatingProjects.length})</TabsTrigger>
          <TabsTrigger value="applications">Мои отклики ({MOCK_APPLICATIONS.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="owned" className="space-y-4">
          {myProjects.length > 0 ? (
            myProjects.map((project) => (
              <Card key={project.id}>
                <CardHeader>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <CardTitle className="text-xl">
                        <Link to={`/projects/${project.id}`} className="hover:text-blue-600">
                          {project.title}
                        </Link>
                      </CardTitle>
                      <CardDescription className="mt-2 line-clamp-2">
                        {project.description}
                      </CardDescription>
                    </div>
                    <Badge variant={project.status === 'active' ? 'default' : 'secondary'}>
                      {project.status === 'active' ? 'Активен' : 'На паузе'}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-6 text-sm text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <Briefcase className="w-4 h-4" />
                        <span>{project.positions.length} вакансий</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Users className="w-4 h-4" />
                        <span>{project.participants.length + 1} участников</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        <span>{formatDistanceToNow(new Date(project.updatedAt), { addSuffix: true, locale: ru })}</span>
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

        <TabsContent value="participating" className="space-y-4">
          {participatingProjects.length > 0 ? (
            participatingProjects.map((project) => (
              <Card key={project.id}>
                <CardHeader>
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <CardTitle className="text-xl">
                        <Link to={`/projects/${project.id}`} className="hover:text-blue-600">
                          {project.title}
                        </Link>
                      </CardTitle>
                      <div className="flex items-center gap-2 mt-2">
                        <Avatar className="w-6 h-6">
                          <AvatarImage src={project.owner.avatar} alt={project.owner.name} />
                          <AvatarFallback>{project.owner.name[0]}</AvatarFallback>
                        </Avatar>
                        <span className="text-sm text-muted-foreground">{project.owner.name}</span>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div className="text-sm text-muted-foreground">
                      Моя роль: <span className="font-medium text-foreground">Участник</span>
                    </div>
                    <Link to={`/projects/${project.id}`}>
                      <Button variant="outline" size="sm">
                        Открыть проект
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            ))
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Users className="w-12 h-12 text-muted-foreground mb-4" />
                <p className="text-muted-foreground mb-4">Вы пока не участвуете в других проектах</p>
                <Link to="/">
                  <Button>Найти проекты</Button>
                </Link>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="applications" className="space-y-4">
          {MOCK_APPLICATIONS.length > 0 ? (
            MOCK_APPLICATIONS.map((application) => {
              const position = MOCK_PROJECTS
                .flatMap(p => p.positions)
                .find(pos => pos.id === application.positionId);
              const project = MOCK_PROJECTS.find(p =>
                p.positions.some(pos => pos.id === application.positionId)
              );

              if (!position || !project) return null;

              return (
                <Card key={application.id}>
                  <CardHeader>
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <CardTitle className="text-lg">{position.title}</CardTitle>
                        <CardDescription className="mt-1">
                          в проекте "{project.title}"
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
                      <div className="text-sm">
                        <span className="text-muted-foreground">Сообщение: </span>
                        {application.message}
                      </div>
                      <div className="flex items-center justify-between text-sm text-muted-foreground">
                        <span>
                          Отправлено {formatDistanceToNow(new Date(application.createdAt), { addSuffix: true, locale: ru })}
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
