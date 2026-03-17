"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import {
  useAcceptInviteMutation,
  useApplicationsQuery,
  useApproveApplicationMutation,
  useCreatePositionMutation,
  useInviteMemberMutation,
  useProjectRolesQuery,
  usePositionsQuery,
  useProjectQuery,
  useRejectApplicationMutation,
  useUpdateMemberPermissionsMutation,
  useUpdateProjectMutation,
} from "@/api/hooks";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { useAuth } from "@/lib/auth/useAuth";
import { extractErrorMessage } from "@/lib/api-error";
import { formatDateTime } from "@/lib/utils";
import type { ApplicationDTO, PositionDTO } from "@/types";

function ProjectDetailContent() {
  const params = useParams();
  const projectId = Number(params.projectId);
  const { data: project, isLoading, error } = useProjectQuery(projectId);
  const { user } = useAuth();
  const projectRoles = useProjectRolesQuery({ page: 1, page_size: 50 });
  const invite = useInviteMemberMutation();
  const accept = useAcceptInviteMutation();
  const updateOverrides = useUpdateMemberPermissionsMutation();
  const updateProject = useUpdateProjectMutation();
  const createPosition = useCreatePositionMutation();
  const approve = useApproveApplicationMutation();
  const reject = useRejectApplicationMutation();

  const positions = usePositionsQuery({ page: 1, page_size: 20 });
  const applications = useApplicationsQuery({ page: 1, page_size: 20 });

  const [inviteUserId, setInviteUserId] = useState<number>(0);
  const roleOptions = useMemo(() => {
    return (projectRoles.data?.items ?? []).map((r) => ({ id: r.id, name: r.name }));
  }, [projectRoles.data?.items]);
  const [inviteRoleId, setInviteRoleId] = useState<number>(0);
  const isOwner = user?.id === project?.owner_id;

  const [editOpen, setEditOpen] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({
    name: "",
    description: "",
    visibility: "public",
    tags: "",
  });

  const [posFormOpen, setPosFormOpen] = useState(false);
  const [posError, setPosError] = useState<string | null>(null);
  const [posForm, setPosForm] = useState({
    title: "",
    description: "",
    responsibilities: "",
    required_skills: "",
    location_type: "remote",
    expected_load: "medium",
  });

  useEffect(() => {
    if (inviteRoleId === 0 && roleOptions.length > 0) {
      setInviteRoleId(roleOptions[0]!.id);
    }
  }, [inviteRoleId, roleOptions]);

  useEffect(() => {
    if (!project) return;
    setEditForm({
      name: project.name ?? "",
      description: project.full_description ?? project.small_description ?? "",
      visibility: project.visibility ?? "public",
      tags: (project.tags ?? []).join(", "),
    });
  }, [project]);

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
        <div className="mt-4 flex flex-wrap gap-2">
          <Link href="/projects" className="btn-secondary text-sm">
            Все проекты
          </Link>
          {isOwner && (
            <button
              className="btn-secondary text-sm"
              type="button"
              onClick={() => setEditOpen((v) => !v)}
            >
              {editOpen ? "Закрыть редактирование" : "Редактировать проект"}
            </button>
          )}
          {isOwner && (
            <button
              className="btn-primary text-sm"
              type="button"
              onClick={() => setPosFormOpen((v) => !v)}
            >
              {posFormOpen ? "Закрыть форму позиции" : "Создать позицию"}
            </button>
          )}
        </div>
      </div>

      {isOwner && editOpen && (
        <div className="card mb-6">
          <h2 className="mb-2 text-lg font-semibold text-gray-900">Редактирование проекта</h2>
          {editError && <div className="mb-3 rounded-md bg-red-50 p-3 text-sm text-red-700">{editError}</div>}
          <div className="grid gap-3 md:grid-cols-2">
            <div className="md:col-span-2">
              <label className="label mb-1">Название</label>
              <input
                className="input"
                value={editForm.name}
                onChange={(e) => setEditForm((p) => ({ ...p, name: e.target.value }))}
              />
            </div>
            <div className="md:col-span-2">
              <label className="label mb-1">Описание</label>
              <textarea
                className="input min-h-28"
                value={editForm.description}
                onChange={(e) => setEditForm((p) => ({ ...p, description: e.target.value }))}
              />
            </div>
            <div>
              <label className="label mb-1">Видимость</label>
              <select
                className="input"
                value={editForm.visibility}
                onChange={(e) => setEditForm((p) => ({ ...p, visibility: e.target.value }))}
              >
                <option value="public">public</option>
                <option value="private">private</option>
              </select>
            </div>
            <div>
              <label className="label mb-1">Теги (через запятую)</label>
              <input
                className="input"
                value={editForm.tags}
                onChange={(e) => setEditForm((p) => ({ ...p, tags: e.target.value }))}
              />
            </div>
            <div className="md:col-span-2">
              <button
                className="btn-primary"
                type="button"
                onClick={async () => {
                  setEditError(null);
                  try {
                    await updateProject.mutateAsync({
                      projectId,
                      body: {
                        name: editForm.name || null,
                        description: editForm.description || null,
                        visibility: editForm.visibility || null,
                        tags: editForm.tags
                          ? editForm.tags.split(",").map((t) => t.trim()).filter(Boolean)
                          : null,
                      },
                    });
                    setEditOpen(false);
                  } catch (err) {
                    setEditError(extractErrorMessage(err, "Не удалось обновить проект"));
                  }
                }}
                disabled={updateProject.isPending}
              >
                {updateProject.isPending ? "Сохранение..." : "Сохранить"}
              </button>
            </div>
          </div>
        </div>
      )}

      {isOwner && posFormOpen && (
        <div className="card mb-6">
          <h2 className="mb-2 text-lg font-semibold text-gray-900">Новая позиция</h2>
          {posError && <div className="mb-3 rounded-md bg-red-50 p-3 text-sm text-red-700">{posError}</div>}
          <div className="grid gap-3 md:grid-cols-2">
            <div className="md:col-span-2">
              <label className="label mb-1">Название</label>
              <input
                className="input"
                value={posForm.title}
                onChange={(e) => setPosForm((p) => ({ ...p, title: e.target.value }))}
              />
            </div>
            <div className="md:col-span-2">
              <label className="label mb-1">Описание</label>
              <textarea
                className="input min-h-28"
                value={posForm.description}
                onChange={(e) => setPosForm((p) => ({ ...p, description: e.target.value }))}
              />
            </div>
            <div className="md:col-span-2">
              <label className="label mb-1">Обязанности (опционально)</label>
              <textarea
                className="input min-h-24"
                value={posForm.responsibilities}
                onChange={(e) => setPosForm((p) => ({ ...p, responsibilities: e.target.value }))}
              />
            </div>
            <div className="md:col-span-2">
              <label className="label mb-1">Навыки (через запятую)</label>
              <input
                className="input"
                value={posForm.required_skills}
                onChange={(e) => setPosForm((p) => ({ ...p, required_skills: e.target.value }))}
                placeholder="react, typescript, postgres"
              />
            </div>
            <div>
              <label className="label mb-1">Формат</label>
              <select
                className="input"
                value={posForm.location_type}
                onChange={(e) => setPosForm((p) => ({ ...p, location_type: e.target.value }))}
              >
                <option value="remote">remote</option>
                <option value="onsite">onsite</option>
                <option value="hybrid">hybrid</option>
              </select>
            </div>
            <div>
              <label className="label mb-1">Загрузка</label>
              <select
                className="input"
                value={posForm.expected_load}
                onChange={(e) => setPosForm((p) => ({ ...p, expected_load: e.target.value }))}
              >
                <option value="low">low</option>
                <option value="medium">medium</option>
                <option value="high">high</option>
              </select>
            </div>
            <div className="md:col-span-2">
              <button
                className="btn-primary"
                type="button"
                onClick={async () => {
                  setPosError(null);
                  try {
                    await createPosition.mutateAsync({
                      projectId,
                      body: {
                        title: posForm.title,
                        description: posForm.description,
                        responsibilities: posForm.responsibilities || null,
                        required_skills: posForm.required_skills
                          ? posForm.required_skills.split(",").map((t) => t.trim()).filter(Boolean)
                          : null,
                        location_type: posForm.location_type || null,
                        expected_load: posForm.expected_load || null,
                      },
                    });
                    setPosFormOpen(false);
                    setPosForm({
                      title: "",
                      description: "",
                      responsibilities: "",
                      required_skills: "",
                      location_type: "remote",
                      expected_load: "medium",
                    });
                  } catch (err) {
                    setPosError(extractErrorMessage(err, "Не удалось создать позицию"));
                  }
                }}
                disabled={createPosition.isPending || !posForm.title || !posForm.description}
              >
                {createPosition.isPending ? "Создание..." : "Создать"}
              </button>
            </div>
          </div>
        </div>
      )}

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
              const isMe = user?.id === member.user_id;
              const canAccept = isMe && member.status !== "active";

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

      <ProjectPositionsSection projectId={projectId} positions={positions.data?.items ?? []} />

      {isOwner && (
        <ProjectApplicationsSection
          projectId={projectId}
          applications={applications.data?.items ?? []}
          onApprove={(id) => approve.mutate({ applicationId: id })}
          onReject={(id) => reject.mutate({ applicationId: id })}
          isMutating={approve.isPending || reject.isPending}
        />
      )}

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

function ProjectPositionsSection({ projectId, positions }: { projectId: number; positions: PositionDTO[] }) {
  const items = useMemo(() => positions.filter((p) => p.project_id === projectId), [positions, projectId]);

  return (
    <div className="card mb-6">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold text-gray-900">Позиции проекта</h2>
        <Link href="/positions" className="text-sm text-brand-700 hover:underline">
          Все позиции
        </Link>
      </div>
      {items.length === 0 ? (
        <p className="text-sm text-gray-500">Пока нет позиций для этого проекта</p>
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {items.map((p) => (
            <Link key={p.id} href={`/positions/${p.id}`} className="rounded-lg border border-gray-100 p-3 hover:border-brand-200">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="font-semibold text-gray-900">{p.title}</div>
                <Badge variant={p.is_open ? "success" : "danger"}>{p.is_open ? "open" : "closed"}</Badge>
              </div>
              <div className="mt-1 text-sm text-gray-600">{p.description.slice(0, 120)}{p.description.length > 120 ? "..." : ""}</div>
              <div className="mt-2 flex flex-wrap gap-2">
                {p.required_skills.slice(0, 6).map((s) => (
                  <Badge key={s} variant="info">
                    {s}
                  </Badge>
                ))}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function ProjectApplicationsSection({
  projectId,
  applications,
  onApprove,
  onReject,
  isMutating,
}: {
  projectId: number;
  applications: ApplicationDTO[];
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
  isMutating: boolean;
}) {
  const items = useMemo(
    () => applications.filter((a) => a.project_id === projectId),
    [applications, projectId],
  );

  return (
    <div className="card mb-6">
      <h2 className="mb-3 text-lg font-semibold text-gray-900">Заявки по проекту</h2>
      {items.length === 0 ? (
        <p className="text-sm text-gray-500">Нет заявок</p>
      ) : (
        <ul className="divide-y divide-gray-100">
          {items.map((a) => (
            <li key={a.id} className="py-3">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge>app #{a.id.slice(0, 8)}</Badge>
                    <Badge>position #{a.position_id.slice(0, 8)}</Badge>
                    <Badge>candidate #{a.candidate_id}</Badge>
                    <Badge variant={a.status === "accepted" ? "success" : a.status === "rejected" ? "danger" : "warning"}>
                      {String(a.status)}
                    </Badge>
                  </div>
                  {a.message && <div className="mt-2 text-sm text-gray-700">{a.message}</div>}
                </div>
                {a.status === "pending" && (
                  <div className="flex gap-2">
                    <button className="btn-primary text-sm" type="button" onClick={() => onApprove(a.id)} disabled={isMutating}>
                      Approve
                    </button>
                    <button
                      className="btn-secondary text-sm hover:border-red-200 hover:text-red-700"
                      type="button"
                      onClick={() => onReject(a.id)}
                      disabled={isMutating}
                    >
                      Reject
                    </button>
                  </div>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
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
