"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { useInviteMemberMutation, useMyProjectsQuery, useProfileQuery, useProjectRolesQuery } from "@/api/hooks";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { extractErrorMessage } from "@/lib/api-error";
import { useAuth } from "@/lib/auth/useAuth";

function ProfilePublicContent() {
  const params = useParams();
  const profileId = Number(params.profileId);
  const { user } = useAuth();

  const profile = useProfileQuery(profileId);

  const myProjects = useMyProjectsQuery({ page: 1, page_size: 50 });
  const projectRoles = useProjectRolesQuery({ page: 1, page_size: 50 });
  const invite = useInviteMemberMutation();

  const availableProjects = useMemo(() => {
    const items = myProjects.data?.items ?? [];
    const myId = user?.id;
    if (!myId) return [];
    return items.filter((p) => {
      if (p.owner_id === myId) return true;
      return (p.memberships ?? []).some((m) => m.user_id === myId && m.status === "active");
    });
  }, [myProjects.data?.items, user?.id]);

  const [selectedProjectId, setSelectedProjectId] = useState<number>(0);
  const [selectedRoleId, setSelectedRoleId] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (selectedProjectId === 0 && availableProjects.length > 0) setSelectedProjectId(availableProjects[0]!.id);
  }, [selectedProjectId, availableProjects]);

  useEffect(() => {
    const items = projectRoles.data?.items ?? [];
    if (selectedRoleId === 0 && items.length > 0) setSelectedRoleId(items[0]!.id);
  }, [selectedRoleId, projectRoles.data?.items]);

  if (profile.isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!profile.data) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="card">
          <h1 className="text-2xl font-bold text-gray-900">Профиль не найден</h1>
          <div className="mt-4">
            <Link href="/profiles" className="btn-secondary">
              К списку профилей
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const p = profile.data;
  const canInvite = !!user && user.id !== p.id;

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{p.display_name ?? `Профиль #${p.id}`}</h1>
          <div className="mt-2 flex flex-wrap gap-2">
            <Badge>profile_id: {p.id}</Badge>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link href="/profiles" className="btn-secondary text-sm">
            Все профили
          </Link>
          <Link href="/projects" className="btn-secondary text-sm">
            Проекты
          </Link>
        </div>
      </div>

      <div className="card">
        {p.specialization && (
          <div>
            <div className="label">Специализация</div>
            <div className="text-gray-700">{p.specialization}</div>
          </div>
        )}
        {p.bio && (
          <div className="mt-4">
            <div className="label">О себе</div>
            <div className="whitespace-pre-wrap text-gray-700">{p.bio}</div>
          </div>
        )}

        {p.skills.length > 0 && (
          <div className="mt-4">
            <div className="label mb-1">Навыки</div>
            <div className="flex flex-wrap gap-2">
              {p.skills.map((s) => (
                <Badge key={s} variant="info">
                  {s}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {p.contacts.length > 0 && (
          <div className="mt-4">
            <div className="label mb-1">Контакты</div>
            <ul className="space-y-1">
              {p.contacts.map((c) => (
                <li key={`${c.provider}-${c.contact}`} className="text-sm text-gray-700">
                  <span className="font-medium">{c.provider}:</span> {c.contact}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {canInvite && (
        <div className="card mt-6">
          <h2 className="text-lg font-semibold text-gray-900">Пригласить в проект</h2>
          <p className="mt-1 text-sm text-gray-600">
            Приглашение использует `profile_id` как `user_id` (они равны).
            Для приглашения применяются <b>project roles</b>.
          </p>

          {error && <div className="mt-3 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div>}

          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <div>
              <div className="label mb-1">Проект (где вы owner или участник)</div>
              <select
                className="input"
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(Number(e.target.value))}
                disabled={myProjects.isLoading || availableProjects.length === 0}
              >
                {availableProjects.length === 0 ? (
                  <option value={0}>Нет проектов</option>
                ) : (
                  availableProjects.map((pr) => (
                    <option key={pr.id} value={pr.id}>
                      {pr.name} (#{pr.id})
                    </option>
                  ))
                )}
              </select>
              {availableProjects.length === 0 && (
                <div className="mt-2 text-sm text-gray-500">
                  Создайте проект, чтобы приглашать кандидатов.{" "}
                  <Link className="text-brand-700 hover:underline" href="/projects/new">
                    Создать проект
                  </Link>
                </div>
              )}
            </div>

            <div>
              <div className="label mb-1">Роль в проекте (project role)</div>
              <select
                className="input"
                value={selectedRoleId}
                onChange={(e) => setSelectedRoleId(Number(e.target.value))}
                disabled={projectRoles.isLoading || (projectRoles.data?.items ?? []).length === 0}
              >
                {(projectRoles.data?.items ?? []).length === 0 ? (
                  <option value={0}>Нет ролей</option>
                ) : (
                  (projectRoles.data?.items ?? []).map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.name} (#{r.id})
                    </option>
                  ))
                )}
              </select>
            </div>
          </div>

          <div className="mt-4">
            <button
              className="btn-primary"
              type="button"
              onClick={async () => {
                setError(null);
                try {
                  await invite.mutateAsync({
                    projectId: selectedProjectId,
                    body: { user_id: p.id, role_id: selectedRoleId },
                  });
                } catch (err) {
                  setError(extractErrorMessage(err, "Не удалось отправить приглашение"));
                }
              }}
              disabled={!selectedProjectId || !selectedRoleId || invite.isPending || availableProjects.length === 0}
            >
              {invite.isPending ? "Отправка..." : "Пригласить"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ProfilePublicPage() {
  return (
    <ProtectedRoute>
      <ProfilePublicContent />
    </ProtectedRoute>
  );
}

