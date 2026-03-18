import { useState } from 'react';
import { useParams, Link } from 'react-router';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { Label } from '../components/ui/label';
import { PositionCard } from '../components/PositionCard';
import { ArrowLeft, Calendar, Users, Target, TrendingUp, CheckCircle2 } from 'lucide-react';
import { MOCK_PROJECTS, CURRENT_USER } from '../data/mockData';
import { formatDistanceToNow } from 'date-fns';
import { ru } from 'date-fns/locale';
import { toast } from 'sonner';

export function ProjectDetailPage() {
  const { id } = useParams();
  const [applicationDialog, setApplicationDialog] = useState(false);
  const [selectedPositionId, setSelectedPositionId] = useState<string | null>(null);
  const [applicationMessage, setApplicationMessage] = useState('');

  const project = MOCK_PROJECTS.find(p => p.id === id);

  if (!project) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Проект не найден</h1>
          <Link to="/">
            <Button>Вернуться на главную</Button>
          </Link>
        </div>
      </div>
    );
  }

  const handleApply = (positionId: string) => {
    setSelectedPositionId(positionId);
    setApplicationDialog(true);
  };

  const handleSubmitApplication = () => {
    toast.success('Отклик отправлен!', {
      description: 'Владелец проекта получит уведомление о вашем отклике.',
    });
    setApplicationDialog(false);
    setApplicationMessage('');
    setSelectedPositionId(null);
  };

  const isOwner = project.ownerId === CURRENT_USER.id;

  return (
    <div className="container mx-auto px-4 py-8">
      <Link to="/">
        <Button variant="ghost" className="mb-6 gap-2">
          <ArrowLeft className="w-4 h-4" />
          Назад к проектам
        </Button>
      </Link>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <CardTitle className="text-3xl mb-2">{project.title}</CardTitle>
                  <div className="flex flex-wrap gap-2 mt-4">
                    {project.tags.map((tag, index) => (
                      <Badge key={index} variant="secondary">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>
                <Badge variant={project.status === 'active' ? 'default' : 'secondary'} className="text-sm">
                  {project.status === 'active' ? 'Активен' : project.status === 'paused' ? 'На паузе' : 'Завершен'}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="about">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="about">О проекте</TabsTrigger>
                  <TabsTrigger value="positions">Вакансии ({project.positions.length})</TabsTrigger>
                  <TabsTrigger value="team">Команда</TabsTrigger>
                </TabsList>

                <TabsContent value="about" className="space-y-6 mt-6">
                  <div>
                    <h3 className="font-semibold mb-2 flex items-center gap-2">
                      <Target className="w-5 h-5 text-blue-600" />
                      Описание
                    </h3>
                    <p className="text-muted-foreground leading-relaxed">{project.description}</p>
                  </div>

                  <div>
                    <h3 className="font-semibold mb-2 flex items-center gap-2">
                      <CheckCircle2 className="w-5 h-5 text-blue-600" />
                      Цели
                    </h3>
                    <p className="text-muted-foreground leading-relaxed">{project.goals}</p>
                  </div>

                  <div>
                    <h3 className="font-semibold mb-2 flex items-center gap-2">
                      <TrendingUp className="w-5 h-5 text-blue-600" />
                      Текущий прогресс
                    </h3>
                    <p className="text-muted-foreground leading-relaxed">{project.progress}</p>
                  </div>
                </TabsContent>

                <TabsContent value="positions" className="space-y-4 mt-6">
                  {project.positions.length > 0 ? (
                    project.positions.map((position) => (
                      <PositionCard
                        key={position.id}
                        position={position}
                        onApply={isOwner ? undefined : () => handleApply(position.id)}
                      />
                    ))
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      Нет открытых вакансий
                    </div>
                  )}
                </TabsContent>

                <TabsContent value="team" className="space-y-4 mt-6">
                  <div className="space-y-3">
                    <Card>
                      <CardContent className="pt-6">
                        <div className="flex items-center gap-4">
                          <Avatar className="w-12 h-12">
                            <AvatarImage src={project.owner.avatar} alt={project.owner.name} />
                            <AvatarFallback>{project.owner.name[0]}</AvatarFallback>
                          </Avatar>
                          <div className="flex-1">
                            <div className="font-semibold">{project.owner.name}</div>
                            <div className="text-sm text-muted-foreground">Владелец проекта</div>
                            {project.owner.bio && (
                              <p className="text-sm text-muted-foreground mt-1">{project.owner.bio}</p>
                            )}
                            <div className="flex flex-wrap gap-1 mt-2">
                              {project.owner.skills.map((skill) => (
                                <Badge key={skill.id} variant="outline" className="text-xs">
                                  {skill.name}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    {project.participants.length === 0 && (
                      <div className="text-center py-8 text-muted-foreground">
                        Пока нет других участников
                      </div>
                    )}
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Информация</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3 text-sm">
                <Calendar className="w-5 h-5 text-muted-foreground" />
                <div>
                  <div className="font-medium">Создан</div>
                  <div className="text-muted-foreground">
                    {formatDistanceToNow(new Date(project.createdAt), { addSuffix: true, locale: ru })}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3 text-sm">
                <Users className="w-5 h-5 text-muted-foreground" />
                <div>
                  <div className="font-medium">Участники</div>
                  <div className="text-muted-foreground">
                    {project.participants.length + 1} человек
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3 text-sm">
                <Target className="w-5 h-5 text-muted-foreground" />
                <div>
                  <div className="font-medium">Открытых вакансий</div>
                  <div className="text-muted-foreground">
                    {project.positions.filter(p => p.status === 'open').length}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {isOwner && (
            <Card className="bg-blue-50 border-blue-200">
              <CardHeader>
                <CardTitle className="text-lg">Управление</CardTitle>
                <CardDescription>Вы владелец этого проекта</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button className="w-full" variant="outline">
                  Редактировать проект
                </Button>
                <Button className="w-full" variant="outline">
                  Добавить вакансию
                </Button>
                <Button className="w-full" variant="outline">
                  Просмотреть отклики
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      <Dialog open={applicationDialog} onOpenChange={setApplicationDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Откликнуться на вакансию</DialogTitle>
            <DialogDescription>
              Расскажите, почему вы хотите присоединиться к проекту
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="message">Сопроводительное сообщение</Label>
              <Textarea
                id="message"
                placeholder="Опишите свой опыт и мотивацию..."
                value={applicationMessage}
                onChange={(e) => setApplicationMessage(e.target.value)}
                rows={5}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setApplicationDialog(false)}>
              Отмена
            </Button>
            <Button onClick={handleSubmitApplication} disabled={!applicationMessage.trim()}>
              Отправить отклик
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
