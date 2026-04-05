export interface PositionDTO {
  id: string;
  project_id: number;
  title: string;
  description: string;
  responsibilities: string | null;
  required_skills: string[];
  is_open: boolean;
  location_type: 'remote' | 'onsite' | 'hybrid';
  expected_load: 'low' | 'medium' | 'high';
}
