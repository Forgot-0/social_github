import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import { Loader2, X } from 'lucide-react';
import { toast } from 'sonner';
import type { ProjectDTO } from '../../api/types';

interface EditProjectDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  project: ProjectDTO | null;
  updateProjectMutation: any;
}

export function EditProjectDialog({ open, onOpenChange, project, updateProjectMutation }: EditProjectDialogProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [visibility, setVisibility] = useState('public');
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');

  useEffect(() => {
    if (project) {
      setName(project.name || '');
      setDescription(project.full_description || project.small_description || '');
      setVisibility(project.visibility || 'public');
      setTags(project.tags || []);
    }
  }, [project, open]);

  const handleAddTag = () => {
    if (tagInput.trim() && !tags.includes(tagInput.trim())) {
      setTags([...tags, tagInput.trim()]);
      setTagInput('');
    }
  };

  const handleRemoveTag = (tag: string) => {
    setTags(tags.filter((t) => t !== tag));
  };

  const handleSubmit = async () => {
    if (!name.trim() || !project) return;

    const data = {
      name: name.trim(),
      description: description.trim() || null,
      visibility: visibility || null,
      tags: tags.length > 0 ? tags : null,
    };

    try {
      await updateProjectMutation.mutateAsync({
        projectId: project.id,
        data,
      });
      toast.success('Проект успешно обновлен!');
      onOpenChange(false);
    } catch (error: any) {
      toast.error('Ошибка при обновлении проекта', {
        description: error?.error?.message || 'Попробуйте позже',
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Редактировать проект</DialogTitle>
          <DialogDescription>
            Обновите информацию о вашем проекте
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="name">Название проекта *</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Название проекта"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Описание</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Подробно опишите ваш проект, цели и задачи"
              rows={6}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="visibility">Видимость</Label>
            <select
              id="visibility"
              value={visibility}
              onChange={(e) => setVisibility(e.target.value)}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <option value="public">Публичный</option>
              <option value="private">Приватный</option>
            </select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="tags">Теги</Label>
            <div className="flex gap-2">
              <Input
                id="tags"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                placeholder="Добавьте тег"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddTag();
                  }
                }}
              />
              <Button type="button" variant="outline" onClick={handleAddTag}>
                Добавить
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
                      className="ml-1 hover:text-destructive"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={updateProjectMutation.isLoading}>
            Отмена
          </Button>
          <Button onClick={handleSubmit} disabled={!name.trim() || updateProjectMutation.isLoading}>
            {updateProjectMutation.isLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Сохранение...
              </>
            ) : (
              'Сохранить'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}