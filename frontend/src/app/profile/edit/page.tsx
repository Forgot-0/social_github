"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import {
  useCreateProfileMutation,
  useProfileQuery,
  useUpdateProfileMutation,
} from "@/api/hooks";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { Spinner } from "@/components/ui/Spinner";
import { extractErrorMessage } from "@/lib/api-error";
import { useAuth } from "@/lib/auth/useAuth";

function EditProfileContent() {
  const router = useRouter();
  const { user } = useAuth();
  const {
    data: existingProfile,
    isLoading: isLoadingProfile,
    isError: profileNotFound,
  } = useProfileQuery(user?.id ?? 0);

  const profileExists = !profileNotFound && !!existingProfile;

  const createProfile = useCreateProfileMutation();
  const updateProfile = useUpdateProfileMutation();

  const [form, setForm] = useState({
    display_name: "",
    bio: "",
    specialization: "",
    skills: "",
    date_birthday: "",
  });
  const [initialized, setInitialized] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (existingProfile && !initialized) {
      setForm({
        display_name: existingProfile.display_name ?? "",
        bio: existingProfile.bio ?? "",
        specialization: existingProfile.specialization ?? "",
        skills: existingProfile.skills.join(", "),
        date_birthday: existingProfile.date_birthday ?? "",
      });
      setInitialized(true);
    }
  }, [existingProfile, initialized]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    const skills = form.skills
      ? form.skills.split(",").map((s) => s.trim()).filter(Boolean)
      : null;

    try {
      if (profileExists) {
        await updateProfile.mutateAsync({
          profileId: existingProfile.id,
          body: {
            display_name: form.display_name || null,
            bio: form.bio || null,
            specialization: form.specialization || null,
            skills,
            date_birthday: form.date_birthday || null,
          },
        });
      } else {
        await createProfile.mutateAsync({
          display_name: form.display_name || null,
          bio: form.bio || null,
          skills,
          date_birthday: form.date_birthday || null,
        });
      }
      router.push("/profile");
    } catch (err) {
      setError(extractErrorMessage(err, "Не удалось сохранить профиль"));
    }
  };

  const updateField = (field: string, value: string) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  if (isLoadingProfile) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="mb-8 text-3xl font-bold text-gray-900">
        {profileExists ? "Редактирование профиля" : "Создание профиля"}
      </h1>

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="display_name" className="label mb-1">Отображаемое имя</label>
          <input
            id="display_name"
            className="input"
            value={form.display_name}
            onChange={(e) => updateField("display_name", e.target.value)}
          />
        </div>

        <div>
          <label htmlFor="specialization" className="label mb-1">Специализация</label>
          <input
            id="specialization"
            className="input"
            value={form.specialization}
            onChange={(e) => updateField("specialization", e.target.value)}
            placeholder="Frontend Developer"
          />
        </div>

        <div>
          <label htmlFor="bio" className="label mb-1">О себе</label>
          <textarea
            id="bio"
            className="input min-h-[100px]"
            value={form.bio}
            onChange={(e) => updateField("bio", e.target.value)}
            rows={4}
          />
        </div>

        <div>
          <label htmlFor="skills" className="label mb-1">Навыки (через запятую)</label>
          <input
            id="skills"
            className="input"
            value={form.skills}
            onChange={(e) => updateField("skills", e.target.value)}
            placeholder="TypeScript, React, Python"
          />
        </div>

        <div>
          <label htmlFor="date_birthday" className="label mb-1">Дата рождения</label>
          <input
            id="date_birthday"
            type="date"
            className="input"
            value={form.date_birthday}
            onChange={(e) => updateField("date_birthday", e.target.value)}
          />
        </div>

        <div className="flex gap-4">
          <button
            type="submit"
            className="btn-primary flex-1"
            disabled={createProfile.isPending || updateProfile.isPending}
          >
            {createProfile.isPending || updateProfile.isPending ? "Сохранение..." : "Сохранить"}
          </button>
          <button type="button" className="btn-secondary" onClick={() => router.back()}>
            Отмена
          </button>
        </div>
      </form>
    </div>
  );
}

export default function EditProfilePage() {
  return (
    <ProtectedRoute>
      <EditProfileContent />
    </ProtectedRoute>
  );
}
