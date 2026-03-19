import { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { useProjectRolesQuery } from '../../api/hooks/useProjectRoles';

interface InviteMemberDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectId: number;
  inviteMemberMutation: any;
}

export function InviteMemberDialog({ open, onOpenChange, projectId, inviteMemberMutation }: InviteMemberDialogProps) {
  const [userId, setUserId] = useState('');
  const [roleId, setRoleId] = useState('');

  const { data: rolesData } = useProjectRolesQuery();
  const roles = rolesData?.items || [];

  const handleSubmit = async () => {
    if (!userId || !roleId) return;

    try {
      await inviteMemberMutation.mutateAsync({
        projectId,
        data: {
          user_id: parseInt(userId),
          role_id: parseInt(roleId),
        },
      });
      toast.success('Приглашение отправлено!', {
        description: 'Пользователь получит уведомление о приглашении.',
      });
      setUserId('');
      setRoleId('');
      onOpenChange(false);
    } catch (error: any) {
      toast.error('Ошибка при отправке приглашения', {
        description: error?.error?.message || 'Попробуйте позже',
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Пригласить участника</DialogTitle>
          <DialogDescription>
            Добавьте нового участника в проект по его ID профиля (ID пользователя = ID профиля)
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="userId">ID пользователя (profile_id) *</Label>
            <Input
              id="userId"
              type="number"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder="Введите ID пользователя"
            />
            <p className="text-xs text-muted-foreground">
              Пользователь может найти свой ID в профиле (profile_id = user_id)
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="role">Роль в проекте *</Label>
            <Select value={roleId} onValueChange={setRoleId}>
              <SelectTrigger id="role">
                <SelectValue placeholder="Выберите роль" />
              </SelectTrigger>
              <SelectContent>
                {roles.map((role) => (
                  <SelectItem key={role.id} value={role.id.toString()}>
                    {role.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={inviteMemberMutation.isLoading}>
            Отмена
          </Button>
          <Button onClick={handleSubmit} disabled={!userId || !roleId || inviteMemberMutation.isLoading}>
            {inviteMemberMutation.isLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Отправка...
              </>
            ) : (
              'Пригласить'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}