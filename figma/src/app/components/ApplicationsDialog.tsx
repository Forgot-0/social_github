import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { Clock, CheckCircle, XCircle, Calendar } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ru } from 'date-fns/locale';
import { useProfileQuery } from '../../api/hooks/useProfiles';
import type { ApplicationDTO } from '../../api/types';
import { getAvatarUrl } from '../utils/avatar';

interface ApplicationsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectId: number;
  selectedPosition: PositionDTO | null;
}

function ApplicationCard({ application, onApprove, onReject, isLoading }: { 
  application: ApplicationDTO; 
  onApprove: () => void;
  onReject: () => void;
  isLoading: boolean;
}) {
  const { data: profile } = useProfileQuery(application.candidate_id);
  
  const displayName = profile?.display_name || `Кандидат ${application.candidate_id}`;
  const avatarUrl = getAvatarUrl(profile?.avatars);

  const statusConfig = {
    pending: { label: 'На рассмотрении', icon: Clock, color: 'bg-yellow-100 text-yellow-800' },
    accepted: { label: 'Принято', icon: CheckCircle, color: 'bg-green-100 text-green-800' },
    rejected: { label: 'Отклонено', icon: XCircle, color: 'bg-red-100 text-red-800' },
  };

  const status = statusConfig[application.status as keyof typeof statusConfig] || statusConfig.pending;
  const StatusIcon = status.icon;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <Avatar className="w-12 h-12">
              <AvatarImage src={avatarUrl} alt={displayName} />
              <AvatarFallback>{displayName[0]?.toUpperCase()}</AvatarFallback>
            </Avatar>
            <div>
              <CardTitle className="text-lg">{displayName}</CardTitle>
              <p className="text-sm text-muted-foreground">
                {profile?.specialization || 'Специализация не указана'}
              </p>
            </div>
          </div>
          <Badge className={status.color}>
            <StatusIcon className="w-3 h-3 mr-1" />
            {status.label}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {application.message && (
          <div>
            <p className="text-sm font-medium mb-1">Сопроводительное письмо:</p>
            <p className="text-sm text-muted-foreground whitespace-pre-wrap">{application.message}</p>
          </div>
        )}

        {profile?.skills && profile.skills.length > 0 && (
          <div>
            <p className="text-sm font-medium mb-2">Навыки:</p>
            <div className="flex flex-wrap gap-2">
              {profile.skills.map((skill, index) => (
                <Badge key={index} variant="outline">
                  {skill}
                </Badge>
              ))}
            </div>
          </div>
        )}

        <div className="text-xs text-muted-foreground">
          {application.decided_at ? (
            `Подано ${formatDistanceToNow(new Date(application.decided_at), { 
              addSuffix: true, 
              locale: ru 
            })}`
          ) : (
            'Недавно'
          )}
        </div>

        {application.status === 'pending' && (
          <div className="flex gap-2 pt-2">
            <Button
              size="sm"
              variant="default"
              onClick={onApprove}
              disabled={isLoading}
              className="flex-1"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Принять
                </>
              )}
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={onReject}
              disabled={isLoading}
              className="flex-1"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  <XCircle className="w-4 h-4 mr-2" />
                  Отклонить
                </>
              )}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function ApplicationsDialog({ open, onOpenChange, projectId, selectedPosition }: ApplicationsDialogProps) {
  const [selectedTab, setSelectedTab] = useState('all');
  
  const { data: applicationsData, isLoading } = usePositionApplicationsQuery(
    selectedPosition?.id || '',
    {},
    { enabled: !!selectedPosition }
  );

  const approveApplicationMutation = useApproveApplicationMutation();
  const rejectApplicationMutation = useRejectApplicationMutation();

  const applications = applicationsData?.items || [];
  const pendingApplications = applications.filter(a => a.status === 'pending');
  const acceptedApplications = applications.filter(a => a.status === 'accepted');
  const rejectedApplications = applications.filter(a => a.status === 'rejected');

  const handleApprove = async (applicationId: string) => {
    try {
      await approveApplicationMutation.mutateAsync(applicationId);
      toast.success('Заявка одобрена!', {
        description: 'Кандидат получит уведомление',
      });
    } catch (error: any) {
      toast.error('Ошибка при одобрении заявки', {
        description: error?.error?.message || 'Попробуйте позже',
      });
    }
  };

  const handleReject = async (applicationId: string) => {
    try {
      await rejectApplicationMutation.mutateAsync(applicationId);
      toast.success('Заявка отклонена');
    } catch (error: any) {
      toast.error('Ошибка при отклонении заявки', {
        description: error?.error?.message || 'Попробуйте позже',
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Отклики на вакансию</DialogTitle>
          <DialogDescription>
            {selectedPosition?.title}
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <Tabs value={selectedTab} onValueChange={setSelectedTab}>
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="all">
                Все ({applications.length})
              </TabsTrigger>
              <TabsTrigger value="pending">
                Ожидают ({pendingApplications.length})
              </TabsTrigger>
              <TabsTrigger value="accepted">
                Принятые ({acceptedApplications.length})
              </TabsTrigger>
              <TabsTrigger value="rejected">
                Отклоненные ({rejectedApplications.length})
              </TabsTrigger>
            </TabsList>

            <TabsContent value="all" className="mt-6 space-y-4">
              {applications.length > 0 ? (
                applications.map((app) => (
                  <ApplicationCard
                    key={app.id}
                    application={app}
                    onApprove={() => handleApprove(app.id)}
                    onReject={() => handleReject(app.id)}
                    isLoading={approveApplicationMutation.isPending || rejectApplicationMutation.isPending}
                  />
                ))
              ) : (
                <div className="text-center py-12">
                  <User className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">Пока нет откликов на эту вакансию</p>
                </div>
              )}
            </TabsContent>

            <TabsContent value="pending" className="mt-6 space-y-4">
              {pendingApplications.length > 0 ? (
                pendingApplications.map((app) => (
                  <ApplicationCard
                    key={app.id}
                    application={app}
                    onApprove={() => handleApprove(app.id)}
                    onReject={() => handleReject(app.id)}
                    isLoading={approveApplicationMutation.isPending || rejectApplicationMutation.isPending}
                  />
                ))
              ) : (
                <div className="text-center py-12">
                  <Clock className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">Нет откликов, ожидающих рассмотрения</p>
                </div>
              )}
            </TabsContent>

            <TabsContent value="accepted" className="mt-6 space-y-4">
              {acceptedApplications.length > 0 ? (
                acceptedApplications.map((app) => (
                  <ApplicationCard
                    key={app.id}
                    application={app}
                    onApprove={() => handleApprove(app.id)}
                    onReject={() => handleReject(app.id)}
                    isLoading={approveApplicationMutation.isPending || rejectApplicationMutation.isPending}
                  />
                ))
              ) : (
                <div className="text-center py-12">
                  <CheckCircle className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">Пока нет принятых откликов</p>
                </div>
              )}
            </TabsContent>

            <TabsContent value="rejected" className="mt-6 space-y-4">
              {rejectedApplications.length > 0 ? (
                rejectedApplications.map((app) => (
                  <ApplicationCard
                    key={app.id}
                    application={app}
                    onApprove={() => handleApprove(app.id)}
                    onReject={() => handleReject(app.id)}
                    isLoading={approveApplicationMutation.isPending || rejectApplicationMutation.isPending}
                  />
                ))
              ) : (
                <div className="text-center py-12">
                  <XCircle className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">Нет отклоненных откликов</p>
                </div>
              )}
            </TabsContent>
          </Tabs>
        )}
      </DialogContent>
    </Dialog>
  );
}