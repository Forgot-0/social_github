import { useState, useEffect } from 'react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Separator } from '../components/ui/separator';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Bell, Shield, User as UserIcon, Camera, Loader2, X, Plus } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '../contexts/AuthContext';
import { useProfileQuery, useUpdateProfileMutation } from '../../api/hooks/useProfiles';
import { AvatarUploadDialog } from '../components/AvatarUploadDialog';
import { getAvatarUrl } from '../utils/avatar';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';

const COMMON_SKILLS = [
  'React', 'TypeScript', 'JavaScript', 'Python', 'Java', 'C++', 'C#',
  'Node.js', 'Django', 'FastAPI', 'Flask', 'Spring Boot',
  'PostgreSQL', 'MongoDB', 'MySQL', 'Redis',
  'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP',
  'Git', 'CI/CD', 'Agile', 'Scrum',
  'UI/UX Design', 'Figma', 'Adobe XD',
  'Machine Learning', 'Data Science', 'AI',
  'Mobile Development', 'iOS', 'Android', 'React Native', 'Flutter',
  'GraphQL', 'REST API', 'Microservices',
  'Testing', 'Jest', 'Pytest', 'Selenium'
];

export function SettingsPage() {
  const { user } = useAuth();
  const { data: profile, isLoading: profileLoading } = useProfileQuery(
    user?.id || 0,
    { enabled: !!user?.id }
  );

  const [displayName, setDisplayName] = useState('');
  const [specialization, setSpecialization] = useState('');
  const [bio, setBio] = useState('');
  const [avatarDialogOpen, setAvatarDialogOpen] = useState(false);
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);
  const [customSkillInput, setCustomSkillInput] = useState('');
  const [showAllSkills, setShowAllSkills] = useState(false);

  const updateProfileMutation = useUpdateProfileMutation();

  useEffect(() => {
    if (profile) {
      setDisplayName(profile.display_name || '');
      setSpecialization(profile.specialization || '');
      setBio(profile.bio || '');
      setSelectedSkills(profile.skills || []);
    }
  }, [profile]);

  const toggleSkill = (skill: string) => {
    setSelectedSkills(prev =>
      prev.includes(skill)
        ? prev.filter(s => s !== skill)
        : [...prev, skill]
    );
  };

  const handleAddCustomSkill = () => {
    const trimmed = customSkillInput.trim();
    if (trimmed && !selectedSkills.includes(trimmed)) {
      setSelectedSkills(prev => [...prev, trimmed]);
      setCustomSkillInput('');
    }
  };

  const handleSaveSkills = () => {
    if (!user) return;

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
          toast.error('Ошибка при обновлении навыков', {
            description: error?.error?.message || 'Попробуйте позже',
          });
        },
      }
    );
  };

  const displayedSkills = showAllSkills ? COMMON_SKILLS : COMMON_SKILLS.slice(0, 15);

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

  const avatarUrl = getAvatarUrl(profile?.avatars);
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
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => setAvatarDialogOpen(true)}
                  >
                    Загрузить фото
                  </Button>
                  <p className="text-xs text-muted-foreground mt-2">
                    JPG, PNG. Макс. 5MB
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
                <Label className="mb-3 block">Добавить свой навык</Label>
                <div className="flex gap-2">
                  <Input
                    placeholder="Введите название навыка..."
                    value={customSkillInput}
                    onChange={(e) => setCustomSkillInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleAddCustomSkill();
                      }
                    }}
                  />
                  <Button onClick={handleAddCustomSkill} variant="outline">
                    <Plus className="w-4 h-4 mr-1" />
                    Добавить
                  </Button>
                </div>
              </div>

              <Separator />

              <div>
                <Label className="mb-3 block">Популярные навыки</Label>
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
      </Tabs>

      <AvatarUploadDialog
        open={avatarDialogOpen}
        onOpenChange={setAvatarDialogOpen}
        currentAvatarUrl={avatarUrl}
        displayName={displayNameValue}
      />
    </div>
  );
}