import { useState } from 'react';
import { useNavigate, Link } from 'react-router';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { ArrowLeft, Plus, X } from 'lucide-react';
import { toast } from 'sonner';

export function CreateProjectPage() {
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [goals, setGoals] = useState('');
  const [progress, setProgress] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');

  const handleAddTag = () => {
    if (tagInput.trim() && !tags.includes(tagInput.trim())) {
      setTags([...tags, tagInput.trim()]);
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter(tag => tag !== tagToRemove));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!title.trim() || !description.trim() || !goals.trim()) {
      toast.error('Заполните все обязательные поля');
      return;
    }

    toast.success('Проект создан!', {
      description: 'Теперь вы можете добавить вакансии',
    });
    
    // Redirect to project page (mock)
    navigate('/my-projects');
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      <Link to="/">
        <Button variant="ghost" className="mb-6 gap-2">
          <ArrowLeft className="w-4 h-4" />
          Назад
        </Button>
      </Link>

      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">Создать новый проект</CardTitle>
          <CardDescription>
            Расскажите о вашем проекте и привлеките участников
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="title">
                Название проекта <span className="text-red-500">*</span>
              </Label>
              <Input
                id="title"
                placeholder="Например: Мобильное приложение для..."
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">
                Описание <span className="text-red-500">*</span>
              </Label>
              <Textarea
                id="description"
                placeholder="Подробно опишите ваш проект, его концепцию и особенности..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={5}
                required
              />
              <p className="text-xs text-muted-foreground">
                Расскажите, что делает ваш проект уникальным
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="goals">
                Цели проекта <span className="text-red-500">*</span>
              </Label>
              <Textarea
                id="goals"
                placeholder="Какие задачи вы планируете решить? Какие результаты хотите достичь?"
                value={goals}
                onChange={(e) => setGoals(e.target.value)}
                rows={4}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="progress">
                Текущий прогресс
              </Label>
              <Textarea
                id="progress"
                placeholder="Что уже реализовано? На каком этапе находится проект?"
                value={progress}
                onChange={(e) => setProgress(e.target.value)}
                rows={3}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="tags">Теги</Label>
              <div className="flex gap-2">
                <Input
                  id="tags"
                  placeholder="Добавьте тег..."
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddTag();
                    }
                  }}
                />
                <Button type="button" onClick={handleAddTag} variant="outline">
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
              {tags.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {tags.map((tag) => (
                    <Badge key={tag} variant="secondary" className="gap-1">
                      {tag}
                      <button
                        type="button"
                        onClick={() => handleRemoveTag(tag)}
                        className="ml-1 hover:text-red-600"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
              )}
              <p className="text-xs text-muted-foreground">
                Теги помогут другим пользователям найти ваш проект
              </p>
            </div>

            <div className="flex gap-3 pt-4">
              <Button type="submit" className="flex-1">
                Создать проект
              </Button>
              <Button type="button" variant="outline" onClick={() => navigate('/')}>
                Отмена
              </Button>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm">
              <p className="font-medium text-blue-900 mb-1">💡 Совет</p>
              <p className="text-blue-700">
                После создания проекта не забудьте добавить вакансии. Это поможет быстрее найти участников команды!
              </p>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
