export interface ApplicationDTO {
  id: string;
  project_id: number;
  position_id: string;
  candidate_id: number;
  status: 'pending' | 'accepted' | 'rejected';
  message: string | null;
  decided_by: number | null;
  decided_at: string | null;
}
