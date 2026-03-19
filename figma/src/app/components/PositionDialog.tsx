import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { Loader2, X } from 'lucide-react';
import { toast } from 'sonner';
import type { PositionDTO } from '../../api/types';

interface PositionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  position?: PositionDTO | null;
  projectId: number;
  createPositionMutation: any;
  updatePositionMutation: any;
}

export function PositionDialog({ open, onOpenChange, position, projectId, createPositionMutation, updatePositionMutation }: PositionDialogProps) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [responsibilities, setResponsibilities] = useState('');
  const [locationType, setLocationType] = useState('remote');
  const [expectedLoad, setExpectedLoad] = useState('medium');
  const [skills, setSkills] = useState<string[]>([]);
  const [skillInput, setSkillInput] = useState('');

  useEffect(() => {
    if (position) {
      setTitle(position.title || '');
      setDescription(position.description || '');
      setResponsibilities(position.responsibilities || '');
      setLocationType(position.location_type || 'remote');
      setExpectedLoad(position.expected_load || 'medium');
      setSkills(position.required_skills || []);
    } else {
      setTitle('');
      setDescription('');
      setResponsibilities('');
      setLocationType('remote');
      setExpectedLoad('medium');
      setSkills([]);
    }
  }, [position, open]);

  const handleAddSkill = () => {
    if (skillInput.trim() && !skills.includes(skillInput.trim())) {
      setSkills([...skills, skillInput.trim()]);
      setSkillInput('');
    }
  };

  const handleRemoveSkill = (skill: string) => {
    setSkills(skills.filter((s) => s !== skill));
  };

  const handleSubmit = async () => {
    const data = {
      title,
      description,
      responsibilities: responsibilities || null,
      required_skills: skills,
      location_type: locationType,
      expected_load: expectedLoad,
    };

    if (position) {
      await updatePositionMutation.mutateAsync({ projectId, positionId: position.id, data });
    } else {
      await createPositionMutation.mutateAsync({ projectId, data });
    }

    onOpenChange(false);
    toast.success(position ? 'Позиция обновлена' : 'Позиция создана');
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{position ? 'Редактировать позицию' : 'Создать позицию'}</DialogTitle>
          <DialogDescription>
            {position ? 'Обновите информацию о позиции' : 'Добавьте новую позицию в проект'}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="title">Название позиции *</Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="например, Frontend разработчик"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Описание *</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Опишите позицию и требования к кандидату"
              rows={4}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="responsibilities">Обязанности</Label>
            <Textarea
              id="responsibilities"
              value={responsibilities}
              onChange={(e) => setResponsibilities(e.target.value)}
              placeholder="Основные обязанности на позиции"
              rows={3}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="location">Формат работы</Label>
              <Select value={locationType} onValueChange={setLocationType}>
                <SelectTrigger id="location">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="remote">Удаленно</SelectItem>
                  <SelectItem value="onsite">В офисе</SelectItem>
                  <SelectItem value="hybrid">Гибрид</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="load">Нагрузка</Label>
              <Select value={expectedLoad} onValueChange={setExpectedLoad}>
                <SelectTrigger id="load">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Низкая</SelectItem>
                  <SelectItem value="medium">Средняя</SelectItem>
                  <SelectItem value="high">Высокая</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="skills">Требуемые навыки</Label>
            <div className="flex gap-2">
              <Input
                id="skills"
                value={skillInput}
                onChange={(e) => setSkillInput(e.target.value)}
                placeholder="Добавьте навык"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddSkill();
                  }
                }}
              />
              <Button type="button" variant="outline" onClick={handleAddSkill}>
                Добавить
              </Button>
            </div>
            {skills.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {skills.map((skill) => (
                  <Badge key={skill} variant="secondary" className="gap-1">
                    {skill}
                    <button
                      type="button"
                      onClick={() => handleRemoveSkill(skill)}
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
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={createPositionMutation.isPending || updatePositionMutation.isPending}>
            Отмена
          </Button>
          <Button onClick={handleSubmit} disabled={!title.trim() || !description.trim() || createPositionMutation.isPending || updatePositionMutation.isPending}>
            {createPositionMutation.isPending || updatePositionMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Сохранение...
              </>
            ) : position ? (
              'Сохранить'
            ) : (
              'Создать'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}