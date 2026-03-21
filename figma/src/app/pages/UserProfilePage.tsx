import { useParams, Link } from 'react-router';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Mail, Briefcase, Loader2, ArrowLeft } from 'lucide-react';
import { useProfileQuery } from '../../api/hooks/useProfiles';
import { useProjectsQuery } from '../../api/hooks/useProjects';
import { ContactsManager } from '../components/ContactsManager';
import { getAvatarUrl } from '../utils/avatar';

export function UserProfilePage() {
  const { id } = useParams<{ id: string }>();
  const profileId = parseInt(id || '0');

  const { data: profile, isLoading } = useProfileQuery(profileId, {
    enabled: !!profileId,
  });

  const { data: projects } = useProjectsQuery({
    userId: profileId,
    enabled: !!profileId,
  });

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8 flex justify-center items-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <p className="text-muted-foreground mb-4">Профиль не найден</p>
            <Link to="/">
              <Button variant="outline">
                <ArrowLeft className="w-4 h-4 mr-2" />
                На главную
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  const displayName = profile.display_name || `User ${profileId}`;
  const avatarUrl = getAvatarUrl(profile.avatars, '256');

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <Link to="/">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Назад
          </Button>
        </Link>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-1 space-y-6">
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-col items-center text-center">
                <Avatar className="w-24 h-24 mb-4">
                  <AvatarImage src={avatarUrl} alt={displayName} />
                  <AvatarFallback className="text-2xl">{displayName[0]?.toUpperCase()}</AvatarFallback>
                </Avatar>
                <h2 className="text-2xl font-bold mb-1">{displayName}</h2>
                {profile.specialization && (
                  <p className="text-sm text-muted-foreground mb-2">{profile.specialization}</p>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">О пользователе</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {profile.bio ? (
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {profile.bio}
                </p>
              ) : (
                <p className="text-sm text-muted-foreground italic">
                  Пользователь не добавил информацию о себе
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Навыки</CardTitle>
            </CardHeader>
            <CardContent>
              {profile.skills && profile.skills.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {profile.skills.map((skill, index) => (
                    <Badge key={index} variant="secondary">
                      {skill}
                    </Badge>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">
                  Навыки не указаны
                </p>
              )}
            </CardContent>
          </Card>

          <ContactsManager
            profileId={profileId}
            contacts={profile.contacts || []}
            editable={false}
          />
        </div>

        <div className="lg:col-span-2">
          <Tabs defaultValue="about">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="about">Информация</TabsTrigger>
              <TabsTrigger value="activity">Активность</TabsTrigger>
            </TabsList>

            <TabsContent value="about" className="mt-6">
              <Card>
                <CardHeader>
                  <CardTitle>Профиль</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div>
                    <h3 className="font-medium mb-2">ID пользоваеля</h3>
                    <p className="text-sm text-muted-foreground">#{profileId}</p>
                  </div>

                  {profile.specialization && (
                    <div>
                      <h3 className="font-medium mb-2">Специализация</h3>
                      <p className="text-sm text-muted-foreground">{profile.specialization}</p>
                    </div>
                  )}

                  {profile.skills && profile.skills.length > 0 && (
                    <div>
                      <h3 className="font-medium mb-2">Навыки и технологии</h3>
                      <div className="flex flex-wrap gap-2">
                        {profile.skills.map((skill, index) => (
                          <Badge key={index} variant="outline">
                            {skill}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {profile.bio && (
                    <div>
                      <h3 className="font-medium mb-2">О себе</h3>
                      <p className="text-sm text-muted-foreground whitespace-pre-wrap">{profile.bio}</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="activity" className="mt-6">
              <Card>
                <CardContent className="py-12 text-center text-muted-foreground">
                  История активности пользователя
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}