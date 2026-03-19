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
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '../components/ui/alert-dialog';
import { ArrowLeft, Calendar, Users, Target, Loader2, Edit, Trash2, Plus, UserPlus } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ru } from 'date-fns/locale';
import { toast } from 'sonner';
import { useAuth } from '../contexts/AuthContext';
import { useProjectQuery, useProjectPositionsQuery, useCreatePositionMutation, useInviteMemberMutation, useUpdateProjectMutation } from '../../api/hooks/useProjects';
import { useProfileQuery } from '../../api/hooks/useProfiles';
import { useCreateApplicationMutation } from '../../api/hooks/useApplications';
import { useUpdatePositionMutation, useDeletePositionMutation } from '../../api/hooks/usePositions';
import { PositionDialog } from '../components/PositionDialog';
import { InviteMemberDialog } from '../components/InviteMemberDialog';
import { EditProjectDialog } from '../components/EditProjectDialog';
import { ApplicationsDialog } from '../components/ApplicationsDialog';
import type { PositionDTO } from '../../api/types';

export function ProjectDetailPage() {
  const { id } = useParams();
  const projectId = parseInt(id || '0');
  
  const [applicationDialog, setApplicationDialog] = useState(false);
  const [selectedPositionId, setSelectedPositionId] = useState<string | null>(null);
  const [applicationMessage, setApplicationMessage] = useState('');
  const [positionDialog, setPositionDialog] = useState(false);
  const [editingPosition, setEditingPosition] = useState<PositionDTO | null>(null);
  const [inviteMemberDialog, setInviteMemberDialog] = useState(false);
  const [deleteAlertOpen, setDeleteAlertOpen] = useState(false);
  const [positionToDelete, setPositionToDelete] = useState<string | null>(null);
  const [editProjectDialog, setEditProjectDialog] = useState(false);
  const [applicationsDialog, setApplicationsDialog] = useState(false);
  const [selectedPositionForApplications, setSelectedPositionForApplications] = useState<PositionDTO | null>(null);

  const { user } = useAuth();
  const { data: project, isLoading: projectLoading } = useProjectQuery(projectId, {
    enabled: !!projectId,
  });
  const { data: positions, isLoading: positionsLoading } = useProjectPositionsQuery(projectId, {
    enabled: !!projectId,
  });
  const { data: ownerProfile } = useProfileQuery(project?.owner_id || 0, {
    enabled: !!project?.owner_id,
  });

  const createApplicationMutation = useCreateApplicationMutation();
  const createPositionMutation = useCreatePositionMutation();
  const updatePositionMutation = useUpdatePositionMutation();
  const deletePositionMutation = useDeletePositionMutation();
  const inviteMemberMutation = useInviteMemberMutation();
  const updateProjectMutation = useUpdateProjectMutation();

  if (projectLoading) {
    return (
      <div className="container mx-auto px-4 py-8 flex justify-center items-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

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
    if (!selectedPositionId) return;

    createApplicationMutation.mutate(
      {
        positionId: selectedPositionId,
        data: { message: applicationMessage },
      },
      {
        onSuccess: () => {
          toast.success('Отклик отправлен!', {
            description: 'Владелец проекта получит уведомление о вашем отклике.',
          });
          setApplicationDialog(false);
          setApplicationMessage('');
          setSelectedPositionId(null);
        },
        onError: (error: any) => {
          toast.error('Ошибка при отправке отклика', {
            description: error?.error?.message || 'Попробуйте позже',
          });
        },
      }
    );
  };

  const handleCreatePosition = () => {
    setEditingPosition(null);
    setPositionDialog(true);
  };

  const handleEditPosition = (position: PositionDTO) => {
    setEditingPosition(position);
    setPositionDialog(true);
  };

  const handleDeletePosition = (positionId: string) => {
    setPositionToDelete(positionId);
    setDeleteAlertOpen(true);
  };

  const handleConfirmDeletePosition = () => {
    if (!positionToDelete) return;

    deletePositionMutation.mutate(
      positionToDelete,
      {
        onSuccess: () => {
          toast.success('Вакансия удалена!', {
            description: 'Вакансия успешно удалена из проекта.',
          });
          setDeleteAlertOpen(false);
          setPositionToDelete(null);
        },
        onError: (error: any) => {
          toast.error('Ошибка при удалении вакансии', {
            description: error?.error?.message || 'Попробуйте позже',
          });
        },
      }
    );
  };

  const handleInviteMember = () => {
    setInviteMemberDialog(true);
  };

  const handleEditProject = () => {
    setEditProjectDialog(true);
  };

  const handleViewApplications = (position: PositionDTO) => {
    setSelectedPositionForApplications(position);
    setApplicationsDialog(true);
  };

  const isOwner = user && project.owner_id === user.id;
  const openPositions = positions?.filter(p => p.is_open) || [];
  const ownerDisplayName = ownerProfile?.display_name || `User ${project.owner_id}`;
  const ownerAvatarUrl = ownerProfile?.avatars?.['medium'] || ownerProfile?.avatars?.['small'] || ownerProfile?.avatars?.['original'];

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
                  <CardTitle className="text-3xl mb-2">{project.name}</CardTitle>
                  {project.tags && project.tags.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-4">
                      {project.tags.map((tag, index) => (
                        <Badge key={index} variant="secondary">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="about">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="about">О проекте</TabsTrigger>
                  <TabsTrigger value="positions">Вакансии ({positions?.length || 0})</TabsTrigger>
                  <TabsTrigger value="team">Команда</TabsTrigger>
                </TabsList>

                <TabsContent value="about" className="space-y-6 mt-6">
                  <div>
                    <h3 className="font-semibold mb-2 flex items-center gap-2">
                      <Target className="w-5 h-5 text-blue-600" />
                      Описание
                    </h3>
                    <p className="text-muted-foreground leading-relaxed">
                      {project.full_description || project.small_description || 'Нет описания'}
                    </p>
                  </div>
                </TabsContent>

                <TabsContent value="positions" className="space-y-4 mt-6">
                  {isOwner && (
                    <Button onClick={handleCreatePosition} className="w-full mb-4 gap-2">
                      <Plus className="w-4 h-4" />
                      Добавить вакансию
                    </Button>
                  )}
                  
                  {positionsLoading ? (
                    <div className="space-y-4">
                      {[1, 2, 3].map((i) => (
                        <Card key={i} className="animate-pulse">
                          <CardHeader>
                            <div className="h-6 bg-gray-200 rounded w-1/3"></div>
                          </CardHeader>
                          <CardContent>
                            <div className="space-y-2">
                              <div className="h-4 bg-gray-200 rounded w-full"></div>
                              <div className="h-4 bg-gray-200 rounded w-2/3"></div>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  ) : positions && positions.length > 0 ? (
                    positions.map((position) => (
                      <Card key={position.id}>
                        <CardHeader>
                          <div className="flex items-start justify-between">
                            <CardTitle className="text-lg">{position.title}</CardTitle>
                            {isOwner && (
                              <div className="flex gap-2">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleEditPosition(position)}
                                >
                                  <Edit className="w-4 h-4" />
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleDeletePosition(position.id)}
                                >
                                  <Trash2 className="w-4 h-4 text-destructive" />
                                </Button>
                              </div>
                            )}
                          </div>
                        </CardHeader>
                        <CardContent>
                          {position.description && (
                            <p className="text-sm text-muted-foreground mb-3">
                              {position.description}
                            </p>
                          )}
                          {position.required_skills && position.required_skills.length > 0 && (
                            <div className="flex flex-wrap gap-2 mb-3">
                              {position.required_skills.map((skill, index) => (
                                <Badge key={index} variant="outline">
                                  {skill}
                                </Badge>
                              ))}
                            </div>
                          )}
                          <div className="flex items-center justify-between">
                            <div className="flex gap-2 text-sm text-muted-foreground">
                              <Badge variant="secondary">{position.location_type}</Badge>
                              <Badge variant="secondary">{position.expected_load}</Badge>
                            </div>
                            <div className="flex gap-2">
                              {isOwner && (
                                <Button size="sm" variant="outline" onClick={() => handleViewApplications(position)}>
                                  Отклики
                                </Button>
                              )}
                              {!isOwner && position.is_open && (
                                <Button size="sm" onClick={() => handleApply(position.id)}>
                                  Откликнуться
                                </Button>
                              )}
                            </div>
                          </div>
                        </CardContent>
                      </Card>
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
                        <Link to={`/users/${project.owner_id}`}>
                          <div className="flex items-center gap-4 hover:bg-muted/50 -m-6 p-6 rounded-lg transition-colors cursor-pointer">
                            <Avatar className="w-12 h-12">
                              <AvatarImage src={ownerAvatarUrl} alt={ownerDisplayName} />
                              <AvatarFallback>{ownerDisplayName[0]?.toUpperCase()}</AvatarFallback>
                            </Avatar>
                            <div className="flex-1">
                              <div className="font-semibold">{ownerDisplayName}</div>
                              <div className="text-sm text-muted-foreground">Владелец проекта</div>
                              {ownerProfile?.bio && (
                                <p className="text-sm text-muted-foreground mt-1">{ownerProfile.bio}</p>
                              )}
                              {ownerProfile?.skills && ownerProfile.skills.length > 0 && (
                                <div className="flex flex-wrap gap-1 mt-2">
                                  {ownerProfile.skills.map((skill, index) => (
                                    <Badge key={index} variant="outline" className="text-xs">
                                      {skill}
                                    </Badge>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        </Link>
                      </CardContent>
                    </Card>

                    {(!project.memberships || project.memberships.length === 0) && (
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
                    {formatDistanceToNow(new Date(project.created_at), { addSuffix: true, locale: ru })}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3 text-sm">
                <Users className="w-5 h-5 text-muted-foreground" />
                <div>
                  <div className="font-medium">Участники</div>
                  <div className="text-muted-foreground">
                    {(project.memberships?.length || 0) + 1} человек
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3 text-sm">
                <Target className="w-5 h-5 text-muted-foreground" />
                <div>
                  <div className="font-medium">Открытых вакансий</div>
                  <div className="text-muted-foreground">
                    {openPositions.length}
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
                <Button className="w-full" variant="outline" onClick={handleEditProject}>
                  Редактировать проект
                </Button>
                <Button className="w-full" variant="outline" onClick={handleCreatePosition}>
                  Добавить вакансию
                </Button>
                <Button className="w-full" variant="outline" onClick={handleInviteMember}>
                  Пригласить участника
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
              <Label htmlFor="message">��опроводительное сообщение</Label>
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
            <Button 
              onClick={handleSubmitApplication} 
              disabled={!applicationMessage.trim() || createApplicationMutation.isPending}
            >
              {createApplicationMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Отправка...
                </>
              ) : (
                'Отправить отклик'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <PositionDialog
        open={positionDialog}
        onOpenChange={setPositionDialog}
        position={editingPosition}
        projectId={projectId}
        createPositionMutation={createPositionMutation}
        updatePositionMutation={updatePositionMutation}
      />

      <InviteMemberDialog
        open={inviteMemberDialog}
        onOpenChange={setInviteMemberDialog}
        projectId={projectId}
        inviteMemberMutation={inviteMemberMutation}
      />

      <AlertDialog open={deleteAlertOpen} onOpenChange={setDeleteAlertOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Удалить вакансию</AlertDialogTitle>
            <AlertDialogDescription>
              Вы уверены, что хотите удалить эту вакансию? Это действие необратимо.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDeletePosition}
              disabled={deletePositionMutation.isPending}
            >
              {deletePositionMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Удаление...
                </>
              ) : (
                'Удалить'
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <EditProjectDialog
        open={editProjectDialog}
        onOpenChange={setEditProjectDialog}
        project={project}
        updateProjectMutation={updateProjectMutation}
      />

      <ApplicationsDialog
        open={applicationsDialog}
        onOpenChange={setApplicationsDialog}
        projectId={projectId}
        selectedPosition={selectedPositionForApplications}
      />
    </div>
  );
}