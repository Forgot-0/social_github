import type { ProfileDTO } from '../../types/api/profile.ts';

export function getProfileAvatarUrl(profile: ProfileDTO | null): string | null {
  if (!profile) return null;

  const avatarGroups = Object.values(profile.avatars ?? {});
  if (avatarGroups.length === 0) return null;

  const lastGroup = avatarGroups[avatarGroups.length - 1];
  const variants = Object.values(lastGroup ?? {});
  if (variants.length === 0) return null;

  return variants[variants.length - 1] ?? null;
}

export function getUserInitials(
  username?: string,
  displayName?: string | null,
): string {
  const base = (displayName || username || 'U').trim();
  if (!base) return 'U';
  return base.slice(0, 1).toUpperCase();
}
