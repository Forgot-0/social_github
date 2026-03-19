import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import { Loader2, X, Plus } from 'lucide-react';
import type { ProfileDTO } from '../../api/types';
import { COMMON_SKILLS } from '../constants/skills';

interface EditProfileDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  profile: ProfileDTO | null | undefined;
  onSave: (data: any) => Promise<void>;
  isLoading?: boolean;
}

export function EditProfileDialog({ open, onOpenChange, profile, onSave, isLoading }: EditProfileDialogProps) {
  const [displayName, setDisplayName] = useState('');
  const [bio, setBio] = useState('');
  const [specialization, setSpecialization] = useState('');
  const [skills, setSkills] = useState<string[]>([]);
  const [skillInput, setSkillInput] = useState('');

  useEffect(() => {
    if (profile) {
      setDisplayName(profile.display_name || '');
      setBio(profile.bio || '');
      setSpecialization(profile.specialization || '');
      setSkills(profile.skills || []);
    }
  }, [profile, open]);

  const handleAddSkill = (skill?: string) => {
    const skillToAdd = skill || skillInput.trim();
    if (skillToAdd && !skills.includes(skillToAdd)) {
      setSkills([...skills, skillToAdd]);
      setSkillInput('');
    }
  };

  const handleRemoveSkill = (skill: string) => {
    setSkills(skills.filter((s) => s !== skill));
  };

  const handleSubmit = async () => {
    const data = {
      display_name: displayName || null,
      bio: bio || null,
      specialization: specialization || null,
      skills: skills.length > 0 ? skills : null,
    };

    await onSave(data);
  };

  // Фильтруем навыки, которые еще не добавлены
  const availableSkills = COMMON_SKILLS.filter(skill => !skills.includes(skill));

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Редактировать профиль</DialogTitle>
          <DialogDescription>
            Обновите информацию о себе
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="displayName">Отображаемое имя</Label>
            <Input
              id="displayName"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="Как вас будут видеть другие"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="specialization">Специализация</Label>
            <Input
              id="specialization"
              value={specialization}
              onChange={(e) => setSpecialization(e.target.value)}
              placeholder="например, Frontend Developer"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="bio">О себе</Label>
            <Textarea
              id="bio"
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              placeholder="Расскажите о себе, своем опыте и интересах"
              rows={5}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="skills">Навыки</Label>
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
            {availableSkills.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {availableSkills.map((skill) => (
                  <Badge key={skill} variant="outline" className="gap-1 cursor-pointer" onClick={() => handleAddSkill(skill)}>
                    {skill}
                    <Plus className="w-3 h-3 ml-1" />
                  </Badge>
                ))}
              </div>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isLoading}>
            Отмена
          </Button>
          <Button onClick={handleSubmit} disabled={isLoading}>
            {isLoading ? (
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