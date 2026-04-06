import { useEffect, useState } from 'react';
import { useAuth } from '../features/auth/auth-context.tsx';
import { listProfiles } from '../services/profiles/profiles.service.ts';
import type { ProfileDTO } from '../types/api/profile.ts';

export function useProfile() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<ProfileDTO | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user?.username) {
      setProfile(null);
      setLoading(false);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);

    let active = true;
    (async () => {
      try {
        const response = await listProfiles({
          username: user.username,
          page_size: 1,
        });
        if (!active) return;
        setProfile(response.items?.[0] ?? null);
      } catch (err) {
        if (active) {
          setError(
            err instanceof Error ? err.message : 'Failed to load profile',
          );
          setProfile(null);
        }
      } finally {
        if (active) setLoading(false);
      }
    })();

    return () => {
      active = false;
    };
  }, [user?.username]);

  return { profile, loading, error };
}
