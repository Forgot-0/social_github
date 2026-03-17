import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { CheckCircle2, Users } from 'lucide-react';
import { Position } from '../types';

interface PositionCardProps {
  position: Position;
  onApply?: () => void;
  showProjectLink?: boolean;
}

export function PositionCard({ position, onApply, showProjectLink = false }: PositionCardProps) {
  const applicationsCount = position.applications.length;
  
  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <CardTitle className="text-lg">{position.title}</CardTitle>
            <CardDescription className="mt-2">{position.description}</CardDescription>
          </div>
          <Badge variant={position.status === 'open' ? 'default' : 'secondary'}>
            {position.status === 'open' ? 'Открыта' : 'Закрыта'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {position.requiredSkills.length > 0 && (
            <div>
              <div className="text-sm font-medium mb-2">Требуемые навыки:</div>
              <div className="flex flex-wrap gap-2">
                {position.requiredSkills.map((skill) => (
                  <Badge key={skill.id} variant="outline" className="gap-1">
                    <CheckCircle2 className="w-3 h-3" />
                    {skill.name}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          <div className="flex items-center justify-between pt-2 border-t">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Users className="w-4 h-4" />
              <span>{applicationsCount} {applicationsCount === 1 ? 'отклик' : 'откликов'}</span>
            </div>

            {position.status === 'open' && onApply && (
              <Button onClick={onApply} size="sm">
                Откликнуться
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
