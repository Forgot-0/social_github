import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Plus, X } from 'lucide-react';
import { api } from '../lib/api';
import { toast } from 'sonner';
import { MarkdownContent } from '../components/MarkdownContent';

function transliterate(value: string) {
  const map: Record<string, string> = {
    а: 'a', б: 'b', в: 'v', г: 'g', д: 'd', е: 'e', ё: 'e', ж: 'zh', з: 'z', и: 'i', й: 'y',
    к: 'k', л: 'l', м: 'm', н: 'n', о: 'o', п: 'p', р: 'r', с: 's', т: 't', у: 'u', ф: 'f',
    х: 'h', ц: 'ts', ч: 'ch', ш: 'sh', щ: 'sch', ъ: '', ы: 'y', ь: '', э: 'e', ю: 'yu', я: 'ya',
  };

  return value
    .toLowerCase()
    .split('')
    .map((char) => map[char] ?? char)
    .join('');
}

export function CreateProject() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    slug: '',
    small_description: '',
    description: '',
    visibility: 'public' as 'public' | 'private',
    tags: [] as string[],
  });
  const [tagInput, setTagInput] = useState('');

  const descriptionPreview = useMemo(() => formData.description.trim(), [formData.description]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name || !formData.slug || !formData.small_description) {
      toast.error('Заполните все обязательные поля');
      return;
    }

    setLoading(true);
    try {
      await api.createProject({
        name: formData.name,
        slug: formData.slug,
        small_description: formData.small_description,
        description: formData.description,
        visibility: formData.visibility,
        tags: formData.tags,
        meta_data: {},
      });

      const createdProjects = await api.getProjects({ slug: formData.slug, page: 1, page_size: 1 });
      const createdProject = Array.isArray(createdProjects?.items) ? createdProjects.items[0] : null;

      toast.success('Проект успешно создан!');
      if (createdProject?.id) {
        navigate(`/projects/${createdProject.id}`);
      } else {
        navigate('/my-projects');
      }
    } catch (error: any) {
      console.error('Failed to create project:', error);
      toast.error(error?.error?.message || 'Ошибка при создании проекта');
    } finally {
      setLoading(false);
    }
  };

  const addTag = () => {
    const tag = tagInput.trim();
    if (tag && !formData.tags.includes(tag)) {
      setFormData({ ...formData, tags: [...formData.tags, tag] });
      setTagInput('');
    }
  };

  const removeTag = (tagToRemove: string) => {
    setFormData({
      ...formData,
      tags: formData.tags.filter((tag) => tag !== tagToRemove),
    });
  };

  const generateSlug = () => {
    const slug = transliterate(formData.name)
      .replace(/[^a-z0-9]+/gi, '-')
      .replace(/^-|-$/g, '');
    setFormData({ ...formData, slug });
  };

  return (
    <div className="py-12">
      <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <button onClick={() => navigate(-1)} className="mb-4 flex items-center space-x-2 text-muted-foreground hover:text-foreground">
            <ArrowLeft className="h-5 w-5" />
            <span>Назад</span>
          </button>
          <h1 className="text-3xl font-bold text-foreground md:text-4xl">Создать проект</h1>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6 rounded-xl border border-border bg-white p-6 shadow-sm">
          <div>
            <label htmlFor="name" className="mb-2 block text-sm font-medium text-foreground">
              Название проекта <span className="text-red-500">*</span>
            </label>
            <input
              id="name"
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              onBlur={generateSlug}
              placeholder="Мой проект"
              className="app-input"
              required
            />
          </div>

          <div>
            <label htmlFor="slug" className="mb-2 block text-sm font-medium text-foreground">
              Slug (URL) <span className="text-red-500">*</span>
            </label>
            <div className="flex gap-2">
              <input
                id="slug"
                type="text"
                value={formData.slug}
                onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                placeholder="moy-proekt"
                className="app-input flex-1"
                pattern="[a-z0-9-]+"
                required
              />
              <button type="button" onClick={generateSlug} className="rounded-xl bg-secondary px-4 py-3 text-secondary-foreground transition-colors hover:bg-accent hover:text-white">
                Сгенерировать
              </button>
            </div>
            <p className="mt-1 text-xs text-muted-foreground">Используется в URL. Только латиница, цифры и дефисы.</p>
          </div>

          <div>
            <label htmlFor="small_description" className="mb-2 block text-sm font-medium text-foreground">
              Краткое описание <span className="text-red-500">*</span>
            </label>
            <textarea
              id="small_description"
              value={formData.small_description}
              onChange={(e) => setFormData({ ...formData, small_description: e.target.value })}
              placeholder="Краткое описание проекта в одном предложении"
              rows={2}
              className="app-textarea min-h-[96px]"
              required
            />
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between gap-3">
              <label htmlFor="description" className="block text-sm font-medium text-foreground">
                Полное описание проекта
              </label>
              <span className="rounded-full bg-secondary px-3 py-1 text-xs text-secondary-foreground">Markdown поддерживается</span>
            </div>
            <textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder={'# О проекте\n\n- Цели\n- Задачи\n- Требования к команде'}
              rows={8}
              className="app-textarea"
            />
            <p className="mt-2 text-sm text-muted-foreground">Можно использовать заголовки, списки, жирный текст, ссылки и блоки кода.</p>
          </div>

          {descriptionPreview && (
            <div className="rounded-xl border border-border bg-secondary/30 p-5">
              <div className="mb-3 text-sm font-medium text-foreground">Предпросмотр описания</div>
              <MarkdownContent content={descriptionPreview} />
            </div>
          )}

          <div>
            <label className="mb-2 block text-sm font-medium text-foreground">Видимость</label>
            <div className="flex flex-wrap gap-4">
              <label className="flex cursor-pointer items-center gap-2 rounded-xl border border-border bg-secondary/30 px-4 py-3">
                <input
                  type="radio"
                  value="public"
                  checked={formData.visibility === 'public'}
                  onChange={(e) => setFormData({ ...formData, visibility: e.target.value as 'public' })}
                  className="h-4 w-4 text-primary focus:ring-primary"
                />
                <span>Публичный</span>
              </label>
              <label className="flex cursor-pointer items-center gap-2 rounded-xl border border-border bg-secondary/30 px-4 py-3">
                <input
                  type="radio"
                  value="private"
                  checked={formData.visibility === 'private'}
                  onChange={(e) => setFormData({ ...formData, visibility: e.target.value as 'private' })}
                  className="h-4 w-4 text-primary focus:ring-primary"
                />
                <span>Приватный</span>
              </label>
            </div>
          </div>

          <div>
            <label htmlFor="tags" className="mb-2 block text-sm font-medium text-foreground">Технологии и теги</label>
            <div className="mb-3 flex gap-2">
              <input
                id="tags"
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addTag();
                  }
                }}
                placeholder="React, TypeScript, Python..."
                className="app-input flex-1"
              />
              <button type="button" onClick={addTag} className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-3 text-white transition-colors hover:bg-accent">
                <Plus className="h-5 w-5" />
                <span>Добавить</span>
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {formData.tags.map((tag) => (
                <span key={tag} className="inline-flex items-center gap-2 rounded-full bg-secondary px-3 py-1 text-secondary-foreground">
                  <span>{tag}</span>
                  <button type="button" onClick={() => removeTag(tag)} className="hover:text-red-500">
                    <X className="h-4 w-4" />
                  </button>
                </span>
              ))}
            </div>
          </div>

          <div className="flex gap-4 pt-4">
            <button type="submit" disabled={loading} className="flex-1 rounded-xl bg-primary py-3 text-white transition-colors hover:bg-accent disabled:cursor-not-allowed disabled:opacity-50">
              {loading ? 'Создание...' : 'Создать проект'}
            </button>
            <button type="button" onClick={() => navigate(-1)} className="rounded-xl border border-border bg-white px-6 py-3 transition-colors hover:bg-secondary">
              Отмена
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
