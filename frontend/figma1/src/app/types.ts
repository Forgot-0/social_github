// Типы данных для платформы

export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  bio?: string;
  skills: Skill[];
  profileOpen: boolean;
  createdAt: string;
}

export interface Skill {
  id: string;
  name: string;
  category: 'frontend' | 'backend' | 'design' | 'management' | 'data' | 'marketing' | 'other';
}

export interface Project {
  id: string;
  title: string;
  description: string;
  goals: string;
  progress: string;
  ownerId: string;
  owner: User;
  positions: Position[];
  participants: Participant[];
  tags: string[];
  createdAt: string;
  updatedAt: string;
  status: 'active' | 'paused' | 'completed';
}

export interface Position {
  id: string;
  projectId: string;
  title: string;
  description: string;
  requiredSkills: Skill[];
  status: 'open' | 'closed';
  applications: Application[];
  createdAt: string;
}

export interface Participant {
  id: string;
  userId: string;
  user: User;
  projectId: string;
  role: string;
  canModerate: boolean;
  joinedAt: string;
}

export interface Application {
  id: string;
  positionId: string;
  userId: string;
  user: User;
  message: string;
  status: 'pending' | 'accepted' | 'rejected';
  createdAt: string;
}

export interface Subscription {
  tier: 'free' | 'pro' | 'enterprise';
  limits: {
    maxProjects: number;
    maxPositionsPerProject: number;
    maxCandidateViews: number;
  };
}
