import { useState } from 'react';
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
import { X, Plus } from 'lucide-react';
import { CURRENT_USER, SKILLS } from '../data/mockData';
import { toast } from 'sonner';

export function SettingsPage() {
  const [name, setName] = useState(CURRENT_USER.name);
  const [email, setEmail] = useState(CURRENT_USER.email);
  const [bio, setBio] = useState(CURRENT_USER.bio || '');
  const [profileOpen, setProfileOpen] = useState(CURRENT_USER.profileOpen);
  const [selectedSkills, setSelectedSkills] = useState<string[]>(
    CURRENT_USER.skills.map(s => s.id)
  );
  const [showAllSkills, setShowAllSkills] = useState(false);

  const handleSaveProfile = () => {
    toast.success('Профиль обновлен!');
  };

  const toggleSkill = (skillId: string) => {
    setSelectedSkills(prev =>
      prev.includes(skillId)
        ? prev.filter(id => id !== skillId)
        : [...prev, skillId]
    );
  };

  const selectedSkillObjects = SKILLS.filter(s => selectedSkills.includes(s.id));
  const displayedSkills = showAllSkills ? SKILLS : SKILLS.slice(0, 10);

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
          <TabsTrigger value="privacy">Приватность</TabsTrigger>
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
                  <AvatarImage src={CURRENT_USER.avatar} alt={CURRENT_USER.name} />
                  <AvatarFallback className="text-xl">{CURRENT_USER.name[0]}</AvatarFallback>
                </Avatar>
                <div>
                  <Button variant="outline" size="sm">Загрузить фото</Button>
                  <p className="text-xs text-muted-foreground mt-2">
                    JPG, PNG. Макс. 2MB
                  </p>
                </div>
              </div>

              <Separator />

              <div className="grid gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Имя</Label>
                  <Input
                    id="name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
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
                <Button onClick={handleSaveProfile}>
                  Сохранить изменения
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
              {selectedSkillObjects.length > 0 && (
                <div>
                  <Label className="mb-3 block">Выбранные навыки ({selectedSkillObjects.length})</Label>
                  <div className="flex flex-wrap gap-2">
                    {selectedSkillObjects.map((skill) => (
                      <Badge key={skill.id} variant="default" className="gap-1 pl-3 pr-2">
                        {skill.name}
                        <button
                          onClick={() => toggleSkill(skill.id)}
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
                    .filter(skill => !selectedSkills.includes(skill.id))
                    .map((skill) => (
                      <Badge
                        key={skill.id}
                        variant="outline"
                        className="cursor-pointer hover:bg-accent"
                        onClick={() => toggleSkill(skill.id)}
                      >
                        <Plus className="w-3 h-3 mr-1" />
                        {skill.name}
                      </Badge>
                    ))}
                </div>
                {!showAllSkills && SKILLS.length > 10 && (
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
                <Button onClick={() => toast.success('Навыки обновлены!')}>
                  Сохранить навыки
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="privacy">
          <Card>
            <CardHeader>
              <CardTitle>Настройки приватности</CardTitle>
              <CardDescription>
                Управляйте видимостью вашего профиля
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <Label htmlFor="profile-open" className="text-base">
                    Открытый профиль
                  </Label>
                  <p className="text-sm text-muted-foreground mt-1">
                    Владельцы проектов смогут видеть ваш профиль и отправлять приглашения
                  </p>
                </div>
                <Switch
                  id="profile-open"
                  checked={profileOpen}
                  onCheckedChange={setProfileOpen}
                />
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <Label htmlFor="email-notifications" className="text-base">
                    Email уведомления
                  </Label>
                  <p className="text-sm text-muted-foreground mt-1">
                    Получайте уведомления о новых откликах и сообщениях
                  </p>
                </div>
                <Switch id="email-notifications" defaultChecked />
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <Label htmlFor="show-skills" className="text-base">
                    Показывать навыки публично
                  </Label>
                  <p className="text-sm text-muted-foreground mt-1">
                    Ваши навыки будут видны в рекомендациях проектов
                  </p>
                </div>
                <Switch id="show-skills" defaultChecked />
              </div>

              <div className="flex justify-end pt-4">
                <Button onClick={() => toast.success('Настройки сохранены!')}>
                  Сохранить настройки
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
                  <div>✓ Персональный менеджер</div>
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
