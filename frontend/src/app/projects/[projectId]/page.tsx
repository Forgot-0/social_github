"use client";

import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { useAcceptInviteMutation, useInviteMemberMutation, useProjectQuery, useRolesQuery, useUpdateMemberPermissionsMutation } from "@/api/hooks";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { useAuth } from "@/lib/auth/useAuth";
import { formatDateTime } from "@/lib/utils";

function ProjectDetailContent() {
  const params = useParams();
  const projectId = Number(params.projectId);
  const { data: project, isLoading, error } = useProjectQuery(projectId);
  const { user } = useAuth();
  const roles = useRolesQuery({ page: 1, page_size: 200 });
  const invite = useInviteMemberMutation();
  const accept = useAcceptInviteMutation();
  const updateOverrides = useUpdateMemberPermissionsMutation();

  const [inviteUserId, setInviteUserId] = useState<number>(0);
  const roleOptions = useMemo(
    () => roles.data?.items.map((r) => ({ id: r.id, name: r.name })) ?? [],
    [roles.data?.items],
  );
  const [inviteRoleId, setInviteRoleId] = useState<number>(0);

  useEffect(() => {
    if (inviteRoleId === 0 && roleOptions.length > 0) {
      setInviteRoleId(roleOptions[0]!.id);
    }
  }, [inviteRoleId, roleOptions]);

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="py-16 text-center">
        <p className="text-lg text-gray-500">Проект не найден</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{project.name}</h1>
            <p className="mt-1 text-sm text-gray-500">/{project.slug}</p>
            <p className="mt-1 text-xs text-gray-400">owner: #{project.owner_id}</p>
          </div>
          <Badge variant={project.visibility === "public" ? "success" : "warning"}>
            {project.visibility === "public" ? "Публичный" : "Приватный"}
          </Badge>
        </div>
      </div>

      {project.full_description && (
        <div className="card mb-6">
          <h2 className="mb-2 text-lg font-semibold text-gray-900">Описание</h2>
          <p className="whitespace-pre-wrap text-gray-700">{project.full_description}</p>
        </div>
      )}

      {project.tags.length > 0 && (
        <div className="mb-6 flex flex-wrap gap-2">
          {project.tags.map((tag) => (
            <Badge key={tag} variant="info">{tag}</Badge>
          ))}
        </div>
      )}

      <div className="card mb-6">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">
          Участники ({project.memberships.length})
        </h2>
        {project.memberships.length === 0 ? (
          <p className="text-sm text-gray-500">Нет участников</p>
        ) : (
          <ul className="divide-y divide-gray-100">
            {project.memberships.map((member) => {
              const isOwner = user?.id === project.owner_id;
              const isMe = user?.id === member.user_id;
              const canAccept = isMe && member.status !== "accepted";

              const overridesJson = JSON.stringify(member.permissions_overrides ?? {}, null, 2);
              return (
                <li key={member.id} className="py-3">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <span className="text-sm text-gray-700">Пользователь #{member.user_id}</span>
                    <div className="flex items-center gap-2">
                      <Badge>{member.status}</Badge>
                      {canAccept && (
                        <button
                          className="btn-primary text-sm"
                          type="button"
                          onClick={() => accept.mutate({ projectId })}
                          disabled={accept.isPending}
                        >
                          Принять приглашение
                        </button>
                      )}
                    </div>
                  </div>

                  {isOwner && (
                    <MemberOverridesEditor
                      keyBase={`${member.id}`}
                      projectId={projectId}
                      userId={member.user_id}
                      initialJson={overridesJson}
                      onSave={(obj) =>
                        updateOverrides.mutate({
                          projectId,
                          userId: member.user_id,
                          body: { permissions_overrides: obj },
                        })
                      }
                      isSaving={updateOverrides.isPending}
                    />
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </div>

      {user?.id === project.owner_id && (
        <div className="card mb-6">
          <h2 className="mb-2 text-lg font-semibold text-gray-900">Пригласить участника</h2>
          <p className="text-sm text-gray-600">
            Минимальный UX: введите `user_id` и выберите роль.
          </p>
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <input
              className="input w-40"
              type="number"
              min={1}
              placeholder="user_id"
              value={inviteUserId || ""}
              onChange={(e) => setInviteUserId(Number(e.target.value))}
            />
            <select
              className="input max-w-xs"
              value={inviteRoleId}
              onChange={(e) => setInviteRoleId(Number(e.target.value))}
            >
              {roleOptions.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name} (#{r.id})
                </option>
              ))}
            </select>
            <button
              className="btn-secondary text-sm"
              type="button"
              onClick={() =>
                invite.mutate({
                  projectId,
                  body: { user_id: inviteUserId, role_id: inviteRoleId },
                })
              }
              disabled={!inviteUserId || !inviteRoleId || invite.isPending}
            >
              Пригласить
            </button>
          </div>
        </div>
      )}

      <div className="text-xs text-gray-400">
        Создан: {formatDateTime(project.created_at)} &middot; Обновлён:{" "}
        {formatDateTime(project.updated_at)}
      </div>
    </div>
  );
}

function MemberOverridesEditor({
  keyBase,
  projectId,
  userId,
  initialJson,
  onSave,
  isSaving,
}: {
  keyBase: string;
  projectId: number;
  userId: number;
  initialJson: string;
  onSave: (obj: Record<string, unknown>) => void;
  isSaving: boolean;
}) {
  const [value, setValue] = useState(initialJson);
  const [error, setError] = useState<string | null>(null);

  const handleSave = () => {
    try {
      const parsed = JSON.parse(value) as Record<string, unknown>;
      setError(null);
      onSave(parsed);
    } catch {
      setError("Некорректный JSON");
    }
  };

  return (
    <div className="mt-3 rounded-md border border-gray-100 bg-gray-50 p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="text-xs font-semibold text-gray-700">
          permissions_overrides для user #{userId}
        </div>
        <button className="btn-secondary text-xs" type="button" onClick={handleSave} disabled={isSaving}>
          Сохранить
        </button>
      </div>
      <textarea
        key={keyBase}
        className="input mt-2 min-h-24 w-full font-mono text-xs"
        value={value}
        onChange={(e) => setValue(e.target.value)}
      />
      {error && <div className="mt-1 text-xs text-red-600">{error}</div>}
      <div className="mt-1 text-[11px] text-gray-500">
        endpoint: PUT /v1/projects/{projectId}/members/{userId}/permissions
      </div>
    </div>
  );
}

export default function ProjectDetailPage() {
  return (
    <ProtectedRoute>
      <ProjectDetailContent />
    </ProtectedRoute>
  );
}
