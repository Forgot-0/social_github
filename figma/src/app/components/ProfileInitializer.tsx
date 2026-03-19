import { useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useProfileQuery, useCreateProfileMutation } from '../../api/hooks/useProfiles';

export function ProfileInitializer() {
  const { user } = useAuth();
  const { data: profile, isError } = useProfileQuery(
    user?.id || 0,
    { 
      enabled: !!user?.id,
      retry: false,
    }
  );

  const createProfileMutation = useCreateProfileMutation();

  useEffect(() => {
    if (user && isError && !profile && !createProfileMutation.isPending) {
      createProfileMutation.mutate({
        display_name: user.username,
        bio: '',
        skills: [],
      });
    }
  }, [user, isError, profile]);

  return null;
}
