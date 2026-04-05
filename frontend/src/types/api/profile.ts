export interface ContactDTO {
  profile_id: number;
  provider: string;
  contact: string;
}

export interface ProfileDTO {
  id: number;
  avatars: Record<number, Record<string, string>>;
  specialization: string | null;
  display_name: string | null;
  bio: string | null;
  date_birthday: string | null;
  skills: string[];
  contacts: ContactDTO[];
}

export interface AvatarPresignResponse {
  url: string;
  fields: Record<string, string>;
  key_base: string;
}
