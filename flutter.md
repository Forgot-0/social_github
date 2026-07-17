# API Documentation — Flutter / AI Frontend Contract

> Canonical contract for the backend implemented under the app/ package. Intended for AI-assisted Flutter frontend generation and for any client that needs to talk to this API reliably.

---

## 1. Global conventions

### Base URL
```text
/api/v1
```

### Authentication
- Protected endpoints require:
```http
Authorization: Bearer <access_token>
```
- Login returns an access token and sets a refresh token cookie named `refresh_token`.
- Refresh is done via `POST /auth/refresh/` using the cookie.
- Logout is done via `POST /auth/logout/`.

### Content types
- `POST /auth/login/` uses `application/x-www-form-urlencoded`.
- All other JSON endpoints use `application/json` unless explicitly noted.
- File uploads are done through presigned URLs; the backend does not expect raw binary upload to the API route.

### Common IDs
- User: `number`
- Project: `number`
- Profile: `number`
- Session: `number`
- Chat: `UUID string`
- Message: `UUID string`
- Position: `UUID string`
- Application: `UUID string`
- Attachment: `UUID string`

### Pagination
Most list endpoints return:
```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20
}
```

Chat list returns:
```json
{
  "has_next": false,
  "chats": [],
  "next_date": null,
  "next_chat_id": null
}
```

Messages list returns:
```json
{
  "messages": [],
  "next_cursor": null,
  "has_next": false
}
```

---

## 2. Core DTOs

```ts
interface AccessTokenResponse {
  access_token: string;
}

interface UserResponse {
  id: number;
  username: string;
  email: string;
}

interface PermissionDTO {
  id: number;
  name: string;
}

interface RoleDTO {
  id: number;
  name: string;
  description: string;
  security_level: number;
  permissions: PermissionDTO[];
}

interface SessionDTO {
  id: number;
  user_id: number;
  device_info: string;
  user_agent: string;
  last_activity: string;
  is_active: boolean;
}

interface UserDTO {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_verified: boolean;
  roles: RoleDTO[];
  permissions: PermissionDTO[];
  sessions: SessionDTO[];
}

interface ContactDTO {
  profile_id: number;
  provider: string;
  contact: string;
}

interface ProfileDTO {
  id: number;
  avatars: Record<number, Record<string, string>>;
  specialization: string | null;
  display_name: string | null;
  bio: string | null;
  date_birthday: string | null;
  skills: string[];
  contacts: ContactDTO[];
}

interface AvatarPresignResponse {
  url: string;
  fields: Record<string, string>;
  key_base: string;
}

interface ProjectRoleDTO {
  id: number;
  name: string;
  permissions: Record<string, unknown>;
}

interface ProjectMemberDTO {
  id: number;
  project_id: number;
  user_id: number;
  role_id: number | null;
  status: string;
  invited_by: number | null;
  joined_at: string | null;
  permissions_overrides: Record<string, unknown>;
  role: ProjectRoleDTO | null;
  project: ProjectDTO | null;
}

interface ProjectDTO {
  id: number;
  owner_id: number;
  name: string;
  slug: string;
  small_description: string | null;
  full_description: string | null;
  visibility: string;
  meta_data: Record<string, unknown>;
  tags: string[];
  created_at: string | null;
  updated_at: string | null;
  memberships: ProjectMemberDTO[];
}

interface PositionDTO {
  id: string;
  project_id: number;
  title: string;
  description: string;
  responsibilities: string | null;
  required_skills: string[];
  is_open: boolean;
  location_type: string;
  expected_load: string;
}

interface ApplicationDTO {
  id: string;
  project_id: number;
  position_id: string;
  candidate_id: number;
  status: 'pending' | 'accepted' | 'rejected';
  message: string | null;
  decided_by: number | null;
  decided_at: string | null;
}

interface ChatDTO {
  id: string;
  seq_counter: number;
  last_activity_at: string | null;
  type: string;
  name: string | null;
  description: string | null;
  avatar_s3_key: string | null;
  is_public: boolean;
  admin_only: boolean;
  slow_mode_seconds: number;
  permissions: Record<string, boolean>;
  created_by: number;
  member_count: number;
  unread_count: number;
}

interface ChatDetailDTO extends Omit<ChatDTO, 'unread_count'> {
  members: Array<{
    user_id: number;
    role_id: number;
    is_muted: boolean;
    is_banned: boolean;
    permissions_overrides: Record<string, boolean>;
  }>;
}

interface AttachmentDTO {
  id: string;
  message_id: string | null;
  chat_id: string;
  uploader_id: number;
  attachment_type: 'image' | 'video' | 'file';
  attachment_status: string;
  url: string | null;
  url_expires_in: number | null;
  s3_key: string;
  mime_type: string;
  original_filename: string;
  size: number;
  width: number | null;
  height: number | null;
  duration_seconds: number | null;
  created_at: string;
}

interface MessageDTO {
  id: string;
  chat_id: string;
  seq: number;
  author_id: number | null;
  type: string;
  content: string | null;
  reply_to_id: string | null;
  forwarded_from_chat_id: string | null;
  forwarded_from_message_id: string | null;
  forwarded_from_author_id: number | null;
  is_edited: boolean;
  created_at: string;
  attachments: AttachmentDTO[];
  reply_to: MessageDTO | null;
  forwarded_from: MessageDTO | null;
}

interface MessagesDTO {
  messages: MessageDTO[];
  next_cursor: number | null;
  has_next: boolean;
}

interface UploadSlotDTO {
  upload_token: string;
  upload_url: string;
  attachment_type: 'image' | 'video' | 'file';
  expires_in: number;
}

interface AttachmentDownloadUrlDTO {
  attachment_id: string;
  url: string;
  expires_in: number;
}

interface JoinTokenDTO {
  token: string;
  slug: string;
  livekit_url: string;
}
```

---

## 3. Auth endpoints

### POST /auth/login/
- Body: `application/x-www-form-urlencoded`
  - `username`
  - `password`
- Response `200`: `AccessTokenResponse`
- Side effect: sets `refresh_token` cookie

### POST /auth/refresh/
- Uses `refresh_token` cookie
- Response `200`: `AccessTokenResponse`

### POST /auth/logout/
- Uses `refresh_token` cookie
- Response `204`

### POST /auth/verifications/email/
- Body: `{ "email": string }`
- Response `204`

### POST /auth/verifications/email/verify/
- Body: `{ "token": string }`
- Response `204`

### POST /auth/password-resets/
- Body: `{ "email": string }`
- Response `204`

### POST /auth/password-resets/confirm/
- Body:
```json
{
  "token": "string",
  "password": "string",
  "password_repeat": "string"
}
```
- Response `204`

### GET /auth/oauth/{provider}/authorize/
- Response `200`: `{ "url": string }`

### GET /auth/oauth/{provider}/authorize/connect/
- Protected
- Response `200`: `{ "url": string }`

### GET /auth/oauth/{provider}/callback/
- Query params: `code`, `state`
- Response `200`: `AccessTokenResponse`

---

## 4. User endpoints

### POST /users/register/
- Body:
```json
{
  "username": "johndoe",
  "email": "user@example.com",
  "password": "Secret1!",
  "password_repeat": "Secret1!"
}
```
- Response `201`: `UserResponse`

### GET /users/me/
- Protected
- Response `200`: `UserResponse`

### GET /users/
- Protected
- Query params: `email`, `username`, `is_active`, `is_verified`, `is_deleted`, `created_after`, `created_before`, `updated_after`, `updated_before`, `has_oauth_accounts`, `has_sessions`, `role_names`, `permission_names`, `page`, `page_size`, `sort`
- Response `200`: `PageResult<UserDTO>`

### GET /users/sessions/
- Protected
- Response `200`: `SessionDTO[]`

---

## 5. Profile endpoints

### GET /profiles/
- Query params: `username`, `display_name`, `skills`, `page`, `page_size`, `sort`
- Response `200`: `PageResult<ProfileDTO>`

### GET /profiles/{profile_id}/
- Response `200`: `ProfileDTO`

### PUT /profiles/{profile_id}/
- Protected
- Body (all optional):
```json
{
  "specialization": "Backend Engineer",
  "display_name": "John Doe",
  "bio": "Loves Python",
  "skills": ["Python", "FastAPI"],
  "date_birthday": "1990-01-15"
}
```
- Response `200`

### POST /profiles/avatar/presign/
- Protected
- Body:
```json
{
  "filename": "avatar.jpg",
  "content_type": "image/jpeg",
  "size": 102400
}
```
- Response `200`: `AvatarPresignResponse`

### POST /profiles/avatar/upload_complete/
- Protected
- Body:
```json
{
  "key_base": "avatars/user_1/avatar",
  "size": 102400,
  "content_type": "image/jpeg"
}
```
- Response `200`: `"OK"`

---

## 6. Project endpoints

### POST /projects/
- Protected
- Body:
```json
{
  "name": "My Project",
  "slug": "my-project",
  "small_description": "Short description",
  "description": "Full description",
  "visibility": "public",
  "tags": ["python", "web"],
  "meta_data": {}
}
```
- Response `201`

### GET /projects/
- Protected
- Query params: `name`, `slug`, `tags`, `page`, `page_size`, `sort`
- Response `200`: `PageResult<ProjectDTO>`

### GET /projects/my/
- Protected
- Query params: `page`, `page_size`
- Response `200`: `PageResult<ProjectDTO>`

### GET /projects/{project_id}/
- Protected
- Response `200`: `ProjectDTO`

### PUT /projects/{project_id}/
- Protected
- Body (all optional):
```json
{
  "name": "Updated Name",
  "description": "Updated description",
  "visibility": "private",
  "tags": ["python"],
  "meta_data": {}
}
```
- Response `200`

### DELETE /projects/{project_id}/
- Protected
- Response `204`

### GET /projects/{project_id}/positions/
- Query params: `title`, `required_skills`, `is_open`, `location_type`, `expected_load`, `page`, `page_size`, `sort`
- Response `200`: `PageResult<PositionDTO>`

### POST /projects/{project_id}/positions/
- Protected
- Body:
```json
{
  "title": "Backend Developer",
  "description": "We need a Python dev",
  "responsibilities": "Build APIs",
  "required_skills": ["Python", "PostgreSQL"],
  "location_type": "remote",
  "expected_load": "high"
}
```
- Response `201`

### POST /projects/{project_id}/invite/
- Protected
- Body:
```json
{
  "user_id": 5,
  "role_id": 2,
  "permissions_overrides": { "write:positions": true }
}
```
- Response `200`

### POST /projects/{project_id}/members/accept/
- Protected
- Response `200`

### PUT /projects/{project_id}/members/{user_id}/permissions/
- Protected
- Body: `{ "permissions_overrides": { "read:applications": true } }`
- Response `200`

### POST /projects/{project_id}/members/{user_id}/role/
- Protected
- Body: `{ "role_id": 2 }`
- Response `200`

---

## 7. Positions and applications

### GET /positions/
- Query params: `project_id`, `title`, `required_skills`, `is_open`, `location_type`, `expected_load`, `page`, `page_size`, `sort`
- Response `200`: `PageResult<PositionDTO>`

### GET /positions/{position_id}/
- Response `200`: `PositionDTO`

### PUT /positions/{position_id}/
- Protected
- Body (all optional): same fields as position create
- Response `200`

### DELETE /positions/{position_id}/
- Protected
- Response `204`

### GET /positions/{position_id}/applications/
- Query params: `project_id`, `candidate_id`, `status`, `page`, `page_size`, `sort`
- Response `200`: `PageResult<ApplicationDTO>`

### POST /positions/{position_id}/applications/
- Protected
- Body: `{ "message": "I'd like to join because..." }`
- Response `201`

### GET /applications/
- Query params: `project_id`, `position_id`, `candidate_id`, `status`, `page`, `page_size`, `sort`
- Response `200`: `PageResult<ApplicationDTO>`

### GET /applications/me/
- Protected
- Query params: `position_id`, `project_id`, `status`, `page`, `page_size`, `sort`
- Response `200`: `PageResult<ApplicationDTO>`

### POST /applications/{application_id}/approve/
- Protected
- Response `200`

### POST /applications/{application_id}/reject/
- Protected
- Response `200`

---

## 8. Roles, permissions, and sessions

### POST /roles/
- Protected
- Body:
```json
{
  "name": "moderator",
  "description": "Can moderate content",
  "security_level": 2,
  "permissions": ["read:chat", "delete:message"]
}
```
- Response `201`

### GET /roles/
- Protected
- Query params: `name`, `security_level`, `min_security_level`, `max_security_level`, `permission_names`, `page`, `page_size`, `sort`
- Response `200`: `PageResult<RoleDTO>`

### POST /roles/{role_name}/permissions/
- Protected
- Body: `{ "permission": ["delete:message"] }`
- Response `200`

### DELETE /roles/{role_name}/permissions/
- Protected
- Body: `{ "permission": ["delete:message"] }`
- Response `200`

### GET /project_roles/
- Query params: `name`, `page`, `page_size`, `sort`
- Response `200`: `PageResult<ProjectRoleDTO>`

### POST /permissions/
- Protected
- Body: `{ "name": "delete:message" }`
- Response `201`

### GET /permissions/
- Protected
- Query params: `name`, `page`, `page_size`, `sort`
- Response `200`: `PageResult<PermissionDTO>`

### DELETE /permissions/{name}/
- Protected
- Response `204`

### GET /sessions/
- Protected
- Query params: `user_id`, `device_id`, `last_activity_after`, `last_activity_before`, `is_active`, `page`, `page_size`, `sort`
- Response `200`: `PageResult<SessionDTO>`

### DELETE /sessions/{session_id}/
- Protected
- Response `204`

---

## 9. Chats, messages, attachments, and calls

### GET /chats/
- Protected
- Query params: `limit`, `last_chat_id`, `last_activity_at`
- Response `200`: `ListChats`

### POST /chats/
- Protected
- Body:
```json
{
  "name": "Team Chat",
  "description": "Our team",
  "chat_type": "group",
  "member_ids": [5, 6],
  "is_public": false,
  "admin_only": false,
  "slow_mode_seconds": 0,
  "permissions": {}
}
```
- Response `201`: `ChatDTO`

### GET /chats/{chat_id}/
- Protected
- Response `200`: `ChatDetailDTO`

### PATCH /chats/{chat_id}/
- Protected
- Body (all optional):
```json
{
  "name": "New name",
  "description": "New description",
  "is_public": true,
  "admin_only": true,
  "slow_mode_seconds": 10,
  "permissions": { "message:send": true }
}
```
- Response `200`: `ChatDTO`

### DELETE /chats/{chat_id}/
- Protected
- Response `204`

### POST /chats/{chat_id}/join/
- Protected
- Response `204`

### POST /chats/{chat_id}/leave/
- Protected
- Response `204`

### GET /chats/{chat_id}/members/
- Protected
- Query params: `limit`, `cursor_user_id`, `include_presence`
- Response `200`: members list

### POST /chats/{chat_id}/members/
- Protected
- Body: `{ "user_id": 7, "role_id": 5 }`
- Response `204`

### PATCH /chats/{chat_id}/members/{user_id}/role/
- Protected
- Body: `{ "role_id": 2 }`
- Response `204`

### PATCH /chats/{chat_id}/members/{user_id}/ban/
- Protected
- Body: `{ "reason": "spam", "bannet_to": "2026-12-31T00:00:00Z" }`
- Response `204`

### DELETE /chats/{chat_id}/members/{user_id}/
- Protected
- Response `204`

### POST /chats/{chat_id}/calls/join/
- Protected
- Response `200`: `JoinTokenDTO`

### POST /chats/{chat_id}/calls/participants/{user_id}/mute/
- Protected
- Body: `{ "muted": true }`
- Response `204`

### GET /chats/{chat_id}/messages/
- Protected
- Query params: `limit`, `cursor_message_seq`
- Response `200`: `MessagesDTO`

### GET /chats/{chat_id}/messages/context/
- Protected
- Query params: `target_seq`, `limit`
- Response `200`: `MessagesDTO`

### POST /chats/{chat_id}/messages/
- Protected
- Supports `Idempotency-Key` header
- Body:
```json
{
  "content": "Hello",
  "reply_to_id": null,
  "message_type": "text",
  "upload_tokens": []
}
```
- Response `201`: `MessageDTO`

### GET /chats/{chat_id}/messages/{message_id}/
- Protected
- Response `200`: `MessageDTO`

### PATCH /chats/{chat_id}/messages/{message_id}/
- Protected
- Body: `{ "content": "Edited text" }`
- Response `200`: `MessageDTO`

### DELETE /chats/{chat_id}/messages/{message_id}/
- Protected
- Response `204`

### POST /chats/{chat_id}/messages/forward/
- Protected
- Body:
```json
{
  "source_chat_id": "550e8400-e29b-41d4-a716-446655440000",
  "source_message_id": "550e8400-e29b-41d4-a716-446655440001",
  "comment": "FYI"
}
```
- Response `201`: `MessageDTO`

### POST /chats/{chat_id}/messages/read/
- Protected
- Body: `{ "message_seq": 120 }`
- Response `204`

### POST /chats/{chat_id}/attachments/upload-requests/
- Protected
- Body:
```json
{
  "uploads": [
    {
      "filename": "photo.png",
      "mime_type": "image/png",
      "file_size": 123456
    }
  ]
}
```
- Response `201`: `UploadSlotDTO[]`

### POST /chats/{chat_id}/attachments/upload-requests/confirm/
- Protected
- Body: `{ "upload_tokens": ["550e8400-e29b-41d4-a716-446655440000"] }`
- Response `202`

### GET /chats/{chat_id}/messages/{message_id}/attachments/{attachment_id}/download-url/
- Protected
- Response `200`: `AttachmentDownloadUrlDTO`

---

## 10. WebSocket contract

### Connection
```text
WS /api/v1/chats/ws/?token=<access_token>
```
- Subprotocol: `chat.v1`

### Server event after connection
```json
{
  "type": "ws.ready",
  "payload": {
    "connection_id": "...",
    "gateway_id": "...",
    "heartbeat_interval": 30,
    "heartbeat_timeout": 90,
    "reconnect": { "mode": "last_seq_per_chat", "op": "resume" }
  }
}
```

### Client commands
```json
{ "op": "subscribe", "chat_id": "<chat_uuid>", "last_seq": 10 }
```
Supported operations:
- `ping`
- `pong`
- `subscribe` (requires `chat_id`)
- `unsubscribe` (requires `chat_id`)
- `resume` (uses `cursors` object)

### WS errors
```json
{ "type": "ws.error", "code": "BAD_COMMAND", "detail": "..." }
```

---

## 11. Error format

```json
{
  "error": {
    "code": "NOT_FOUND_USER",
    "message": "User not found",
    "detail": { "user_id": 42 }
  },
  "status": 404,
  "request_id": "...",
  "timestamp": 1743400000.123
}
```

Common error codes:
- `WRONG_LOGIN_DATA`
- `INVALID_TOKEN`
- `EXPIRED_TOKEN`
- `PASSWORD_MISMATCH`
- `DUPLICATE_USER`
- `DUPLICATE_ROLE`
- `NOT_FOUND_USER`
- `NOT_FOUND_ROLE`
- `NOT_FOUND_PERMISSIONS`
- `NOT_FOUND_PROFILE`
- `NOT_FOUND_PROJECT`
- `NOT_FOUND_OR_INACTIVE_SESSION`
- `ACCESS_DENIED`
- `VALIDATION_EXCEPTION`
- `LINKED_ANOTHER_USER_OAUTH`
- `OAUTH_STATE_NOT_FOUND`
- `NOT_EXIST_PROVIDER_OAUTH`

---

## 12. Flutter / AI generation guidance

Use this document as the source of truth for generating a Flutter client.

### Recommended architecture
- `AuthRepository`
- `UserRepository`
- `ProfileRepository`
- `ProjectRepository`
- `ChatRepository`
- `WebSocketClient`

### Important implementation notes
1. Store access tokens securely and refresh them with the interceptor on `401/403`.
2. For login, use form data or `application/x-www-form-urlencoded`.
3. For avatar/attachment uploads, use the presigned URL returned by the backend.
4. Use UUID parsing for chat/message IDs and `DateTime` parsing for timestamps.
5. Treat the backend as the authority for request/response shapes; do not invent fields that are not documented here.

### Prompt-ready summary
When generating Flutter code from this document, assume:
- Base URL: `/api/v1`
- Auth strategy: login -> store access token -> refresh via cookie -> retry failed requests
- Domains: auth, users, profiles, projects, positions, applications, roles, sessions, chats
- Real-time layer: WebSocket for chat events
