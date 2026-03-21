import { Link } from 'react-router';
import { useState } from 'react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Mail, Briefcase, Loader2, Camera, Pencil, Edit } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ru } from 'date-fns/locale';
import { toast } from 'sonner';
import { useAuth } from '../contexts/AuthContext';
import { useProfileQuery, useUpdateProfileMutation } from '../../api/hooks/useProfiles';
import { useMyProjectsQuery } from '../../api/hooks/useProjects';
import { EditProfileDialog } from '../components/EditProfileDialog';
import { AvatarUploadDialog } from '../components/AvatarUploadDialog';
import { ContactsManager } from '../components/ContactsManager';

export function ProfilePage() {
  const { user } = useAuth();
  const { data: profile, isLoading: profileLoading } = useProfileQuery(
    user?.id || 0,
    { enabled: !!user?.id }
  );
  const { data: projectsData, isLoading: projectsLoading } = useMyProjectsQuery();

  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isAvatarDialogOpen, setIsAvatarDialogOpen] = useState(false);
  const [isEditingSkills, setIsEditingSkills] = useState(false);
  const updateProfileMutation = useUpdateProfileMutation();

  const handleSaveProfile = async (data: any) => {
    if (!user?.id) return;

    try {
      await updateProfileMutation.mutateAsync({
        profileId: user.id,
        data,
      });
      toast.success('Профиль успешно обновлен');
      setIsEditDialogOpen(false);
    } catch (error: any) {
      toast.error('Ошибка при обновлении профиля', {
        description: error?.error?.message || 'Попробуйте позже',
      });
    }
  };

  const handleEditSkills = () => {
    setIsEditingSkills(false);
    setIsEditDialogOpen(true);
  };

  if (profileLoading) {
    return (
      <div className="container mx-auto px-4 py-8 flex justify-center items-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const projects = projectsData?.items || [];
  const displayName = profile?.display_name || user?.username || 'User';
  // Исправлено: avatars теперь Record<string, string>, где значение - это уже URL
  const avatarUrl = profile?.avatars?.['medium'] || profile?.avatars?.['small'] || profile?.avatars?.['original'];

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-1 space-y-6">
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-col items-center text-center">
                <div className="relative mb-4">
                  <Avatar className="w-24 h-24">
                    <AvatarImage src={avatarUrl} alt={displayName} />
                    <AvatarFallback className="text-2xl">{displayName[0]?.toUpperCase()}</AvatarFallback>
                  </Avatar>
                  <Button
                    size="sm"
                    variant="secondary"
                    className="absolute -bottom-2 -right-2 rounded-full w-8 h-8 p-0"
                    onClick={() => setIsAvatarDialogOpen(true)}
                  >
                    <Camera className="w-4 h-4" />
                  </Button>
                </div>
                <h2 className="text-2xl font-bold mb-1">{displayName}</h2>
                {profile?.specialization && (
                  <p className="text-sm text-muted-foreground mb-2">{profile.specialization}</p>
                )}
                <p className="text-muted-foreground mb-4">{user?.email}</p>
                
                <Button 
                  variant="outline" 
                  className="w-full gap-2"
                  onClick={() => setIsEditDialogOpen(true)}
                >
                  <Edit className="w-4 h-4" />
                  Редактировать профиль
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">О себе</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {profile?.bio && (
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {profile.bio}
                </p>
              )}

              <div className="space-y-3 text-sm">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Mail className="w-4 h-4" />
                  <span>{user?.email}</span>
                </div>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Briefcase className="w-4 h-4" />
                  <span>{projects.length} {projects.length === 1 ? 'проект' : 'проектов'}</span>
                </div>
              </div>

              <div className="pt-4 border-t">
                <p className="text-xs text-muted-foreground mb-1">Ваш ID профиля:</p>
                <code className="text-sm bg-muted px-2 py-1 rounded">{user?.id}</code>
                <p className="text-xs text-muted-foreground mt-1">
                  profile_id = user_id
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Навыки</CardTitle>
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-8 w-8 p-0"
                  onClick={() => setIsEditDialogOpen(true)}
                >
                  <Pencil className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {profile && profile.skills && profile.skills.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {profile.skills.map((skill, index) => (
                    <Badge key={index} variant="secondary">
                      {skill}
                    </Badge>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">
                  Добавьте навыки через редактирование профиля
                </p>
              )}
            </CardContent>
          </Card>

          <ContactsManager
            profileId={user?.id || 0}
            contacts={profile?.contacts || []}
            editable={true}
          />
        </div>

        <div className="lg:col-span-2">
          <Tabs defaultValue="projects">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="projects">Проекты ({projects.length})</TabsTrigger>
              <TabsTrigger value="activity">Активность</TabsTrigger>
            </TabsList>

            <TabsContent value="projects" className="mt-6 space-y-6">
              {projectsLoading ? (
                <div className="flex justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
                </div>
              ) : projects.length > 0 ? (
                <div className="grid gap-6">
                  {projects.map((project) => (
                    <Card key={project.id}>
                      <CardHeader>
                        <Link to={`/projects/${project.id}`}>
                          <CardTitle className="hover:text-blue-600 transition-colors">
                            {project.name}
                          </CardTitle>
                        </Link>
                      </CardHeader>
                      <CardContent>
                        {project.small_description && (
                          <p className="text-sm text-muted-foreground mb-3">
                            {project.small_description}
                          </p>
                        )}
                        {project.tags && project.tags.length > 0 && (
                          <div className="flex flex-wrap gap-2">
                            {project.tags.map((tag, index) => (
                              <Badge key={index} variant="secondary">
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </CardContent>
                    </Card>
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

      <EditProfileDialog
        open={isEditDialogOpen}
        onOpenChange={setIsEditDialogOpen}
        profile={profile}
        onSave={handleSaveProfile}
        isLoading={updateProfileMutation.isPending}
      />

      <AvatarUploadDialog
        open={isAvatarDialogOpen}
        onOpenChange={setIsAvatarDialogOpen}
        currentAvatarUrl={avatarUrl}
        displayName={displayName}
      />
    </div>
  );
}