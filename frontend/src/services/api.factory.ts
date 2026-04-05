import {
  createFetchHttpClient,
  resolveApiBasePath,
} from '../infrastructure/http/fetch-http-client';
import type { IHttpClient } from '../application/ports/http-client.port';
import { ApplicationsService } from './applications.service';
import { AuthService } from './auth.service';
import { ChatsService } from './chats.service';
import { MessagesService } from './messages.service';
import { PositionsService } from './positions.service';
import { ProfilesService } from './profiles.service';
import { ProjectsService } from './projects.service';
import { RolesService } from './roles.service';
import { SessionsService } from './sessions.service';
import { UsersService } from './users.service';

export interface ApiServicesOptions {
  /** Defaults to `VITE_API_BASE_URL` + `/api/v1` (see `resolveApiBasePath`). */
  basePath?: string;
  getAccessToken?: () => string | null;
  credentials?: RequestCredentials;
}

export interface ApiServices {
  readonly basePath: string;
  readonly http: IHttpClient;
  readonly auth: AuthService;
  readonly users: UsersService;
  readonly profiles: ProfilesService;
  readonly projects: ProjectsService;
  readonly positions: PositionsService;
  readonly applications: ApplicationsService;
  readonly roles: RolesService;
  readonly sessions: SessionsService;
  readonly chats: ChatsService;
  readonly messages: MessagesService;
}

export function createApiServices(
  options: ApiServicesOptions = {},
): ApiServices {
  const basePath = options.basePath ?? resolveApiBasePath();
  const http = createFetchHttpClient({
    basePath,
    getAccessToken: options.getAccessToken,
    credentials: options.credentials,
  });

  return {
    basePath,
    http,
    auth: new AuthService(http),
    users: new UsersService(http),
    profiles: new ProfilesService(http),
    projects: new ProjectsService(http),
    positions: new PositionsService(http),
    applications: new ApplicationsService(http),
    roles: new RolesService(http),
    sessions: new SessionsService(http),
    chats: new ChatsService(http),
    messages: new MessagesService(http),
  };
}

/** Default API bundle (same-origin `/api/v1` unless `VITE_API_BASE_URL` is set). */
export const api = createApiServices();
