import { Link, useParams } from 'react-router';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Badge } from '../components/ui/badge';
import { ArrowLeft, Calendar, Users, Loader2 } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ru } from 'date-fns/locale';
import { useAuth } from '../contexts/AuthContext';
import { useProjectQuery } from '../../api/hooks/useProjects';
import { useProfileQuery } from '../../api/hooks/useProfiles';
import { useProjectRoleQuery } from '../../api/hooks/useProjectRoles';
import { getAvatarUrl } from '../utils/avatar';

// Компонент для отображения участника проекта
function TeamMember({ userId, roleId, isOwner = false }: { userId: number; roleId?: number | null; isOwner?: boolean }) {
  const { data: profile, isLoading: profileLoading } = useProfileQuery(userId, {
    enabled: !!userId,
  });
  
  const { data: role, isLoading: roleLoading } = useProjectRoleQuery(roleId, {
    enabled: !!roleId,
  });

  if (profileLoading || roleLoading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4 animate-pulse">
            <div className="w-12 h-12 rounded-full bg-gray-200"></div>
            <div className="flex-1">
              <div className="h-4 bg-gray-200 rounded w-1/3 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2"></div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!profile) {
    return null;
  }

  const displayName = profile.display_name || `User ${userId}`;
  const avatarUrl = getAvatarUrl(profile.avatars, '64');
  const roleName = isOwner ? 'Владелец проекта' : (role?.name || 'Участник');

  return (
    <Card>
      <CardContent className="pt-6">
        <Link to={`/users/${userId}`}>
          <div className="flex items-center gap-4 hover:bg-muted/50 -m-6 p-6 rounded-lg transition-colors cursor-pointer">
            <Avatar className="w-12 h-12">
              <AvatarImage src={avatarUrl} alt={displayName} />
              <AvatarFallback>{displayName[0]?.toUpperCase()}</AvatarFallback>
            </Avatar>
            <div className="flex-1">
              <div className="font-semibold">{displayName}</div>
              <div className="text-sm text-muted-foreground">{roleName}</div>
              {profile.specialization && (
                <p className="text-sm text-muted-foreground mt-1">{profile.specialization}</p>
              )}
              {profile.skills && profile.skills.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {profile.skills.slice(0, 5).map((skill, index) => (
                    <Badge key={index} variant="outline" className="text-xs">
                      {skill}
                    </Badge>
                  ))}
                  {profile.skills.length > 5 && (
                    <Badge variant="outline" className="text-xs">
                      +{profile.skills.length - 5}
                    </Badge>
                  )}
                </div>
              )}
            </div>
          </div>
        </Link>
      </CardContent>
    </Card>
  );
}

export function ProjectDetailPage() {
  const { id } = useParams();
  const projectId = parseInt(id || '0');

  const { user } = useAuth();
  const { data: project, isLoading: projectLoading } = useProjectQuery(projectId, {
    enabled: !!projectId,
  });
  const { data: ownerProfile } = useProfileQuery(project?.owner_id || 0, {
    enabled: !!project?.owner_id,
  });

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

  const isOwner = user && project.owner_id === user.id;

  return (
    <div className="container mx-auto px-4 py-8">
      <Link to="/">
        <Button variant="ghost" className="mb-6 gap-2">
          <ArrowLeft className="w-4 h-4" />
          Назад к проектам
        </Button>
      </Link>

      <div className="grid gap-6">
        <Card>
          <CardHeader>
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
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold mb-2">Описание</h3>
                <p className="text-muted-foreground leading-relaxed">
                  {project.full_description || project.small_description || 'Нет описания'}
                </p>
              </div>

              <div className="flex items-center gap-6 text-sm">
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-muted-foreground" />
                  <span className="text-muted-foreground">
                    Создан {project.created_at ? formatDistanceToNow(new Date(project.created_at), { addSuffix: true, locale: ru }) : 'Н/Д'}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-muted-foreground" />
                  <span className="text-muted-foreground">
                    {(project.memberships?.length || 0)} участников
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Команда</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {/* Остальные участники */}
              {project.memberships && project.memberships.length > 0 ? (
                project.memberships.map((member) => (
                  <TeamMember 
                    key={member.id} 
                    userId={member.user_id} 
                    roleId={member.role_id}
                  />
                ))
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  Пока нет других участников
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
