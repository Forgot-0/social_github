import { Link } from 'react-router';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { ProjectCard } from '../components/ProjectCard';
import { Mail, MapPin, Calendar, Edit, Briefcase, Award } from 'lucide-react';
import { CURRENT_USER, MOCK_PROJECTS } from '../data/mockData';
import { formatDistanceToNow } from 'date-fns';
import { ru } from 'date-fns/locale';

export function ProfilePage() {
  const myProjects = MOCK_PROJECTS.filter(p => p.ownerId === CURRENT_USER.id);
  const participatingProjects = MOCK_PROJECTS.filter(p =>
    p.participants.some(part => part.userId === CURRENT_USER.id)
  );

  const allProjects = [...myProjects, ...participatingProjects];

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-1 space-y-6">
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-col items-center text-center">
                <Avatar className="w-24 h-24 mb-4">
                  <AvatarImage src={CURRENT_USER.avatar} alt={CURRENT_USER.name} />
                  <AvatarFallback className="text-2xl">{CURRENT_USER.name[0]}</AvatarFallback>
                </Avatar>
                <h2 className="text-2xl font-bold mb-1">{CURRENT_USER.name}</h2>
                <p className="text-muted-foreground mb-4">{CURRENT_USER.email}</p>
                
                <Link to="/settings" className="w-full">
                  <Button variant="outline" className="w-full gap-2">
                    <Edit className="w-4 h-4" />
                    Редактировать профиль
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">О себе</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {CURRENT_USER.bio && (
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {CURRENT_USER.bio}
                </p>
              )}

              <div className="space-y-3 text-sm">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Mail className="w-4 h-4" />
                  <span>{CURRENT_USER.email}</span>
                </div>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Calendar className="w-4 h-4" />
                  <span>
                    Зарегистрирован {formatDistanceToNow(new Date(CURRENT_USER.createdAt), { addSuffix: true, locale: ru })}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Briefcase className="w-4 h-4" />
                  <span>{allProjects.length} проектов</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Award className="w-5 h-5" />
                Навыки
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {CURRENT_USER.skills.map((skill) => (
                  <Badge key={skill.id} variant="secondary">
                    {skill.name}
                  </Badge>
                ))}
              </div>
              {CURRENT_USER.skills.length === 0 && (
                <p className="text-sm text-muted-foreground">
                  Добавьте навыки в настройках профиля
                </p>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="lg:col-span-2">
          <Tabs defaultValue="projects">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="projects">Проекты ({allProjects.length})</TabsTrigger>
              <TabsTrigger value="activity">Активность</TabsTrigger>
            </TabsList>

            <TabsContent value="projects" className="mt-6 space-y-6">
              {allProjects.length > 0 ? (
                <div className="grid gap-6">
                  {allProjects.map((project) => (
                    <ProjectCard key={project.id} project={project} />
                  ))}
                </div>
              ) : (
                <Card>
                  <CardContent className="flex flex-col items-center justify-center py-12">
                    <Briefcase className="w-12 h-12 text-muted-foreground mb-4" />
                    <p className="text-muted-foreground mb-4">
                      У вас пока нет проектов
                    </p>
                    <Link to="/create-project">
                      <Button>Создать проект</Button>
                    </Link>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            <TabsContent value="activity" className="mt-6">
              <Card>
                <CardContent className="py-12 text-center text-muted-foreground">
                  История активности появится здесь
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
