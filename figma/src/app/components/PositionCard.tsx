import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { CheckCircle2, ExternalLink } from 'lucide-react';
import { PositionDTO } from '../../api/types';
import { Link } from 'react-router';

interface PositionCardProps {
  position: PositionDTO;
  onApply?: () => void;
  projectId?: number;
  showProjectLink?: boolean;
}

export function PositionCard({ position, onApply, projectId, showProjectLink = false }: PositionCardProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <CardTitle className="text-lg">{position.title}</CardTitle>
            <CardDescription className="mt-2">{position.description}</CardDescription>
          </div>
          <Badge variant={position.is_open ? 'default' : 'secondary'}>
            {position.is_open ? 'Открыта' : 'Закрыта'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {position.required_skills && position.required_skills.length > 0 && (
            <div>
              <div className="text-sm font-medium mb-2">Требуемые навыки:</div>
              <div className="flex flex-wrap gap-2">
                {position.required_skills.map((skill, index) => (
                  <Badge key={`${skill}-${index}`} variant="outline" className="gap-1">
                    <CheckCircle2 className="w-3 h-3" />
                    {skill}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          <div className="flex items-center justify-between pt-2 border-t">
            <div className="flex gap-2">
              {showProjectLink && projectId && (
                <Link to={`/projects/${projectId}`}>
                  <Button variant="outline" size="sm" className="gap-2">
                    <ExternalLink className="w-4 h-4" />
                    Перейти к проекту
                  </Button>
                </Link>
              )}
            </div>

            {position.is_open && onApply && (
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
