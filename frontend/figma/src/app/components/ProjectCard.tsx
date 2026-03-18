import { Link } from 'react-router';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { Button } from './ui/button';
import { Briefcase, Calendar, Users } from 'lucide-react';
import { Project } from '../types';
import { formatDistanceToNow } from 'date-fns';
import { ru } from 'date-fns/locale';

interface ProjectCardProps {
  project: Project;
}

export function ProjectCard({ project }: ProjectCardProps) {
  const openPositionsCount = project.positions.filter(p => p.status === 'open').length;
  
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <CardTitle className="text-xl mb-2">
              <Link to={`/projects/${project.id}`} className="hover:text-blue-600 transition-colors">
                {project.title}
              </Link>
            </CardTitle>
            <CardDescription className="line-clamp-2">
              {project.description}
            </CardDescription>
          </div>
          <Badge variant={project.status === 'active' ? 'default' : 'secondary'}>
            {project.status === 'active' ? 'Активен' : project.status === 'paused' ? 'На паузе' : 'Завершен'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {project.tags.map((tag, index) => (
              <Badge key={index} variant="outline">
                {tag}
              </Badge>
            ))}
          </div>

          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <div className="flex items-center gap-1">
              <Briefcase className="w-4 h-4" />
              <span>{openPositionsCount} {openPositionsCount === 1 ? 'вакансия' : 'вакансий'}</span>
            </div>
            <div className="flex items-center gap-1">
              <Users className="w-4 h-4" />
              <span>{project.participants.length} {project.participants.length === 1 ? 'участник' : 'участников'}</span>
            </div>
            <div className="flex items-center gap-1">
              <Calendar className="w-4 h-4" />
              <span>{formatDistanceToNow(new Date(project.createdAt), { addSuffix: true, locale: ru })}</span>
            </div>
          </div>

          <div className="flex items-center justify-between pt-2 border-t">
            <div className="flex items-center gap-2">
              <Avatar className="w-8 h-8">
                <AvatarImage src={project.owner.avatar} alt={project.owner.name} />
                <AvatarFallback>{project.owner.name[0]}</AvatarFallback>
              </Avatar>
              <div className="text-sm">
                <div className="font-medium">{project.owner.name}</div>
                <div className="text-muted-foreground text-xs">Владелец</div>
              </div>
            </div>

            <Link to={`/projects/${project.id}`}>
              <Button variant="outline" size="sm">
                Подробнее
              </Button>
            </Link>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
