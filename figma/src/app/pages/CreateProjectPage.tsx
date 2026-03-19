import { useState } from 'react';
import { useNavigate, Link } from 'react-router';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { ArrowLeft, Plus, X, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { useCreateProjectMutation } from '../../api/hooks';

export function CreateProjectPage() {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [smallDescription, setSmallDescription] = useState('');
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');
  
  const createProjectMutation = useCreateProjectMutation({
    onSuccess: () => {
      toast.success('Проект создан!', {
        description: 'Теперь вы можете добавить позиции',
      });
      navigate('/my-projects');
    },
    onError: (error: any) => {
      toast.error('Ошибка при создании проекта', {
        description: error.response?.data?.error?.message || 'Попробуйте еще раз',
      });
    },
  });

  const handleAddTag = () => {
    if (tagInput.trim() && !tags.includes(tagInput.trim())) {
      setTags([...tags, tagInput.trim()]);
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter(tag => tag !== tagToRemove));
  };

  const generateSlug = (text: string) => {
    return text
      .toLowerCase()
      .replace(/[^a-z0-9а-я]+/g, '-')
      .replace(/^-|-$/g, '');
  };

  const handleNameChange = (value: string) => {
    setName(value);
    if (!slug) {
      setSlug(generateSlug(value));
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!name.trim() || !slug.trim() || !description.trim()) {
      toast.error('Заполните все обязательные поля');
      return;
    }

    createProjectMutation.mutate({
      name: name.trim(),
      slug: slug.trim(),
      small_description: smallDescription.trim() || null,
      description: description.trim(),
      visibility: 'public',
      tags: tags.length > 0 ? tags : null,
    });
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
              <Label htmlFor="name">
                Название проекта <span className="text-red-500">*</span>
              </Label>
              <Input
                id="name"
                placeholder="Например: Мобильное приложение для..."
                value={name}
                onChange={(e) => handleNameChange(e.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="slug">
                URL проекта <span className="text-red-500">*</span>
              </Label>
              <Input
                id="slug"
                placeholder="Например: mobilnoe-prilozhenie"
                value={slug}
                onChange={(e) => setSlug(e.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="smallDescription">
                Короткое описание
              </Label>
              <Textarea
                id="smallDescription"
                placeholder="Кратко опишите ваш проект..."
                value={smallDescription}
                onChange={(e) => setSmallDescription(e.target.value)}
                rows={2}
              />
              <p className="text-xs text-muted-foreground">
                Это описание будет отображаться в списке проектов
              </p>
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
                {createProjectMutation.isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  'Создать проект'
                )}
              </Button>
              <Button type="button" variant="outline" onClick={() => navigate('/')}>
                Отмена
              </Button>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm">
              <p className="font-medium text-blue-900 mb-1">💡 Совет</p>
              <p className="text-blue-700">
                После создания проекта не забудьте добавить позиции. Это поможет быстрее найти участников команды!
              </p>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}