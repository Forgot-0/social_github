import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { Loader2, Plus, X, Mail, MessageCircle, Link as LinkIcon, Github, Linkedin } from 'lucide-react';
import { toast } from 'sonner';
import { useAddContactMutation, useRemoveContactMutation } from '../../api/hooks/useProfiles';
import type { ContactDTO } from '../../api/types';

interface ContactsManagerProps {
  profileId: number;
  contacts: ContactDTO[];
  editable?: boolean;
}

const CONTACT_PROVIDERS = [
  { value: 'email', label: 'Email', icon: Mail },
  { value: 'telegram', label: 'Telegram', icon: MessageCircle },
  { value: 'github', label: 'GitHub', icon: Github },
  { value: 'linkedin', label: 'LinkedIn', icon: Linkedin },
  { value: 'website', label: 'Website', icon: LinkIcon },
  { value: 'other', label: 'Другое', icon: LinkIcon },
];

export function ContactsManager({ profileId, contacts, editable = false }: ContactsManagerProps) {
  const [isAdding, setIsAdding] = useState(false);
  const [provider, setProvider] = useState('');
  const [contact, setContact] = useState('');

  const addContactMutation = useAddContactMutation();
  const removeContactMutation = useRemoveContactMutation();

  const handleAddContact = async () => {
    if (!provider || !contact.trim()) {
      toast.error('Заполните все поля');
      return;
    }

    try {
      await addContactMutation.mutateAsync({
        profileId,
        data: { provider, contact: contact.trim() },
      });
      toast.success('Контакт добавлен');
      setProvider('');
      setContact('');
      setIsAdding(false);
    } catch (error: any) {
      toast.error('Ошибка при добавлении контакта', {
        description: error?.error?.message || 'Попробуйте позже',
      });
    }
  };

  const handleRemoveContact = async (providerContact: string) => {
    try {
      await removeContactMutation.mutateAsync({
        profileId,
        provideContact: providerContact,
      });
      toast.success('Контакт удален');
    } catch (error: any) {
      toast.error('Ошибка при удалении контакта', {
        description: error?.error?.message || 'Попробуйте позже',
      });
    }
  };

  const getProviderIcon = (providerName: string) => {
    const provider = CONTACT_PROVIDERS.find((p) => p.value === providerName.toLowerCase());
    const Icon = provider?.icon || LinkIcon;
    return <Icon className="w-4 h-4" />;
  };

  const getProviderLabel = (providerName: string) => {
    const provider = CONTACT_PROVIDERS.find((p) => p.value === providerName.toLowerCase());
    return provider?.label || providerName;
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Контакты</CardTitle>
          {editable && !isAdding && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsAdding(true)}
            >
              <Plus className="w-4 h-4 mr-2" />
              Добавить
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {isAdding && editable && (
          <div className="space-y-3 p-4 border rounded-lg bg-muted/30">
            <div className="space-y-2">
              <Label htmlFor="provider">Тип контакта</Label>
              <Select value={provider} onValueChange={setProvider}>
                <SelectTrigger id="provider">
                  <SelectValue placeholder="Выберите тип" />
                </SelectTrigger>
                <SelectContent>
                  {CONTACT_PROVIDERS.map((p) => {
                    const Icon = p.icon;
                    return (
                      <SelectItem key={p.value} value={p.value}>
                        <div className="flex items-center gap-2">
                          <Icon className="w-4 h-4" />
                          {p.label}
                        </div>
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="contact">Контакт</Label>
              <Input
                id="contact"
                value={contact}
                onChange={(e) => setContact(e.target.value)}
                placeholder="например, @username или email@example.com"
              />
            </div>

            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setIsAdding(false);
                  setProvider('');
                  setContact('');
                }}
                disabled={addContactMutation.isPending}
              >
                Отмена
              </Button>
              <Button
                size="sm"
                onClick={handleAddContact}
                disabled={!provider || !contact.trim() || addContactMutation.isPending}
              >
                {addContactMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Добавление...
                  </>
                ) : (
                  'Добавить'
                )}
              </Button>
            </div>
          </div>
        )}

        {contacts && contacts.length > 0 ? (
          <div className="space-y-2">
            {contacts.map((c, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <div className="text-muted-foreground flex-shrink-0">
                    {getProviderIcon(c.provider)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-muted-foreground">
                      {getProviderLabel(c.provider)}
                    </p>
                    <p className="text-sm truncate">{c.contact}</p>
                  </div>
                </div>
                {editable && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRemoveContact(`${c.provider}/${c.contact}`)}
                    disabled={removeContactMutation.isPending}
                  >
                    <X className="w-4 h-4 text-muted-foreground hover:text-destructive" />
                  </Button>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground text-center py-4">
            {editable ? 'Добавьте контакты для связи' : 'Контакты не указаны'}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
