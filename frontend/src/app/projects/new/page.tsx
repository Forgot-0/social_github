"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { useCreateProjectMutation } from "@/api/hooks";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { extractErrorMessage } from "@/lib/api-error";

function CreateProjectContent() {
  const router = useRouter();
  const createProject = useCreateProjectMutation();

  const [form, setForm] = useState({
    name: "",
    slug: "",
    description: "",
    visibility: "public",
    tags: "",
  });
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault(); 
    setError(null);

    try {
      await createProject.mutateAsync({
        name: form.name,
        slug: form.slug,
        description: form.description || null,
        visibility: form.visibility,
        tags: form.tags ? form.tags.split(",").map((t) => t.trim()) : null,
      });
      router.push("/dashboard");
    } catch (err) {
      setError(extractErrorMessage(err, "Не удалось создать проект"));
    }
  };

  const updateField = (field: string, value: string) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  return (
    <div className="mx-auto max-w-2xl px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="mb-8 text-3xl font-bold text-gray-900">Новый проект</h1>

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="name" className="label mb-1">Название проекта</label>
          <input
            id="name"
            className="input"
            value={form.name}
            onChange={(e) => updateField("name", e.target.value)}
            required
          />
        </div>

        <div>
          <label htmlFor="slug" className="label mb-1">Slug (URL)</label>
          <input
            id="slug"
            className="input"
            value={form.slug}
            onChange={(e) => updateField("slug", e.target.value)}
            required
            placeholder="my-project"
          />
        </div>

        <div>
          <label htmlFor="description" className="label mb-1">Описание</label>
          <textarea
            id="description"
            className="input min-h-[120px]"
            value={form.description}
            onChange={(e) => updateField("description", e.target.value)}
            rows={4}
          />
        </div>

        <div>
          <label htmlFor="visibility" className="label mb-1">Видимость</label>
          <select
            id="visibility"
            className="input"
            value={form.visibility}
            onChange={(e) => updateField("visibility", e.target.value)}
          >
            <option value="public">Публичный</option>
            <option value="private">Приватный</option>
          </select>
        </div>

        <div>
          <label htmlFor="tags" className="label mb-1">
            Теги (через запятую)
          </label>
          <input
            id="tags"
            className="input"
            value={form.tags}
            onChange={(e) => updateField("tags", e.target.value)}
            placeholder="react, typescript, backend"
          />
        </div>

        <button type="submit" className="btn-primary w-full" disabled={createProject.isPending}>
          {createProject.isPending ? "Создание..." : "Создать проект"}
        </button>
      </form>
    </div>
  );
}

export default function CreateProjectPage() {
  return (
    <ProtectedRoute>
      <CreateProjectContent />
    </ProtectedRoute>
  );
}
