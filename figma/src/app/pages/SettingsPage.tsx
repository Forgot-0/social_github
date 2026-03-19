import { useState, useEffect } from 'react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Switch } from '../components/ui/switch';
import { Separator } from '../components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { X, Plus, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '../contexts/AuthContext';
import { useProfileQuery, useUpdateProfileMutation } from '../../api/hooks/useProfiles';
import { COMMON_SKILLS } from '../constants/skills';

export function SettingsPage() {
  const { user } = useAuth();
  const { data: profile, isLoading: profileLoading } = useProfileQuery(
    user?.id || 0,
    { enabled: !!user?.id }
  );
  const updateProfileMutation = useUpdateProfileMutation();

  const [displayName, setDisplayName] = useState('');
  const [specialization, setSpecialization] = useState('');
  const [bio, setBio] = useState('');
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);
  const [showAllSkills, setShowAllSkills] = useState(false);

  useEffect(() => {
    if (profile) {
      setDisplayName(profile.display_name || '');
      setSpecialization(profile.specialization || '');
      setBio(profile.bio || '');
      setSelectedSkills(profile.skills || []);
    }
  }, [profile]);

  const handleSaveProfile = () => {
    if (!user || !profile) return;

    updateProfileMutation.mutate(
      {
        profileId: user.id,
        data: {
          display_name: displayName,
          specialization,
          bio,
        },
      },
      {
        onSuccess: () => {
          toast.success('Профиль обновлен!');
        },
        onError: (error: any) => {
          toast.error('Ошибка при обновлении профиля', {
            description: error?.error?.message || 'Попробуйте позже',
          });
        },
      }
    );
  };

  const handleSaveSkills = () => {
    if (!user || !profile) return;

    updateProfileMutation.mutate(
      {
        profileId: user.id,
        data: {
          skills: selectedSkills,
        },
      },
      {
        onSuccess: () => {
          toast.success('Навыки обновлены!');
        },
        onError: (error: any) => {
          toast.error('Ошибка при обнов��ении навыков', {
            description: error?.error?.message || 'Попробуйте позже',
          });
        },
      }
    );
  };

  const toggleSkill = (skill: string) => {
    setSelectedSkills(prev =>
      prev.includes(skill)
        ? prev.filter(s => s !== skill)
        : [...prev, skill]
    );
  };

  const displayedSkills = showAllSkills ? COMMON_SKILLS : COMMON_SKILLS.slice(0, 15);

  if (profileLoading) {
    return (
      <div className="container mx-auto px-4 py-8 flex justify-center items-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">Пожалуйста, войдите в систему</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const avatarUrl = profile?.avatars?.['medium'] || profile?.avatars?.['small'] || profile?.avatars?.['original'];
  const displayNameValue = profile?.display_name || user.username;

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Настройки</h1>
        <p className="text-muted-foreground">
          Управляйте своим профилем и предпочтениями
        </p>
      </div>

      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList>
          <TabsTrigger value="profile">Профиль</TabsTrigger>
          <TabsTrigger value="skills">Навыки</TabsTrigger>
          <TabsTrigger value="subscription">Подписка</TabsTrigger>
        </TabsList>

        <TabsContent value="profile">
          <Card>
            <CardHeader>
              <CardTitle>Информация профиля</CardTitle>
              <CardDescription>
                Обновите свои личные данные
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center gap-6">
                <Avatar className="w-20 h-20">
                  <AvatarImage src={avatarUrl} alt={displayNameValue} />
                  <AvatarFallback className="text-xl">{displayNameValue[0]?.toUpperCase()}</AvatarFallback>
                </Avatar>
                <div>
                  <Button variant="outline" size="sm" disabled>Загрузить фото</Button>
                  <p className="text-xs text-muted-foreground mt-2">
                    JPG, PNG. Макс. 2MB
                  </p>
                </div>
              </div>

              <Separator />

              <div className="grid gap-4">
                <div className="space-y-2">
                  <Label htmlFor="username">Username</Label>
                  <Input
                    id="username"
                    value={user.username}
                    disabled
                  />
                  <p className="text-xs text-muted-foreground">
                    Username нельзя изменить
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={user.email}
                    disabled
                  />
                  <p className="text-xs text-muted-foreground">
                    Email нельзя изменить
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="displayName">Отображаемое имя</Label>
                  <Input
                    id="displayName"
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    placeholder="Как вас называть?"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="specialization">Специализация</Label>
                  <Input
                    id="specialization"
                    value={specialization}
                    onChange={(e) => setSpecialization(e.target.value)}
                    placeholder="Например: Frontend Developer"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="bio">О себе</Label>
                  <Textarea
                    id="bio"
                    value={bio}
                    onChange={(e) => setBio(e.target.value)}
                    rows={4}
                    placeholder="Расскажите о себе, своем опыте и интересах..."
                  />
                  <p className="text-xs text-muted-foreground">
                    {bio.length}/500 символов
                  </p>
                </div>
              </div>

              <div className="flex justify-end">
                <Button 
                  onClick={handleSaveProfile}
                  disabled={updateProfileMutation.isPending}
                >
                  {updateProfileMutation.isPending ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Сохранение...
                    </>
                  ) : (
                    'Сохранить изменения'
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="skills">
          <Card>
            <CardHeader>
              <CardTitle>Мои навыки</CardTitle>
              <CardDescription>
                Добавьте навыки для получения персональных рекомендаций
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {selectedSkills.length > 0 && (
                <div>
                  <Label className="mb-3 block">Выбранные навыки ({selectedSkills.length})</Label>
                  <div className="flex flex-wrap gap-2">
                    {selectedSkills.map((skill) => (
                      <Badge key={skill} variant="default" className="gap-1 pl-3 pr-2">
                        {skill}
                        <button
                          onClick={() => toggleSkill(skill)}
                          className="ml-1 hover:text-red-300"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              <Separator />

              <div>
                <Label className="mb-3 block">Доступные навыки</Label>
                <div className="flex flex-wrap gap-2">
                  {displayedSkills
                    .filter(skill => !selectedSkills.includes(skill))
                    .map((skill) => (
                      <Badge
                        key={skill}
                        variant="outline"
                        className="cursor-pointer hover:bg-accent"
                        onClick={() => toggleSkill(skill)}
                      >
                        <Plus className="w-3 h-3 mr-1" />
                        {skill}
                      </Badge>
                    ))}
                </div>
                {!showAllSkills && COMMON_SKILLS.length > 15 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowAllSkills(true)}
                    className="mt-3"
                  >
                    Показать все навыки
                  </Button>
                )}
              </div>

              <div className="flex justify-end pt-4">
                <Button 
                  onClick={handleSaveSkills}
                  disabled={updateProfileMutation.isPending}
                >
                  {updateProfileMutation.isPending ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Сохранение...
                    </>
                  ) : (
                    'Сохранить навыки'
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="subscription">
          <div className="grid gap-6 md:grid-cols-3">
            <Card className="border-2">
              <CardHeader>
                <CardTitle>Free</CardTitle>
                <CardDescription>Для начинающих</CardDescription>
                <div className="mt-4">
                  <span className="text-3xl font-bold">$0</span>
                  <span className="text-muted-foreground">/месяц</span>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2 text-sm">
                  <div>✓ 2 проекта</div>
                  <div>✓ 3 вакансии на проект</div>
                  <div>✓ 10 просмотров кандидатов</div>
                  <div>✓ Базовая поддержка</div>
                </div>
                <Button variant="outline" className="w-full" disabled>
                  Текущий план
                </Button>
              </CardContent>
            </Card>

            <Card className="border-2 border-blue-600 relative">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                <Badge className="bg-blue-600">Популярный</Badge>
              </div>
              <CardHeader>
                <CardTitle>Pro</CardTitle>
                <CardDescription>Для активных пользователей</CardDescription>
                <div className="mt-4">
                  <span className="text-3xl font-bold">$9</span>
                  <span className="text-muted-foreground">/месяц</span>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2 text-sm">
                  <div>✓ 10 проектов</div>
                  <div>✓ 10 вакансий на проект</div>
                  <div>✓ 100 просмотров кандидатов</div>
                  <div>✓ Приоритетная поддержка</div>
                  <div>✓ Аналитика проектов</div>
                </div>
                <Button className="w-full">
                  Перейти на Pro
                </Button>
              </CardContent>
            </Card>

            <Card className="border-2">
              <CardHeader>
                <CardTitle>Enterprise</CardTitle>
                <CardDescription>Для компаний</CardDescription>
                <div className="mt-4">
                  <span className="text-3xl font-bold">$29</span>
                  <span className="text-muted-foreground">/месяц</span>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2 text-sm">
                  <div>✓ Неограниченные проекты</div>
                  <div>✓ Неограниченные вакансии</div>
                  <div>✓ Неограниченные просмотры</div>
                  <div>✓ Персональный менежер</div>
                  <div>✓ API доступ</div>
                </div>
                <Button variant="outline" className="w-full">
                  Связаться с нами
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}