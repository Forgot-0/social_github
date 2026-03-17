"use client";

import { useParams } from "next/navigation";

import { useProjectQuery } from "@/api/hooks";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { formatDateTime } from "@/lib/utils";

function ProjectDetailContent() {
  const params = useParams();
  const projectId = Number(params.projectId);
  const { data: project, isLoading, error } = useProjectQuery(projectId);

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
            {project.memberships.map((member) => (
              <li key={member.id} className="flex items-center justify-between py-3">
                <span className="text-sm text-gray-700">
                  Пользователь #{member.user_id}
                </span>
                <Badge>{member.status}</Badge>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="text-xs text-gray-400">
        Создан: {formatDateTime(project.created_at)} &middot; Обновлён:{" "}
        {formatDateTime(project.updated_at)}
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
