export interface JoinTokenDTO {
  token: string;
  slug: string;
  livekit_url: string;
}

export interface LiveKitParticipantsDTO {
  identity: string;
  name: string;
  state: number;
  joined_at: number;
}
