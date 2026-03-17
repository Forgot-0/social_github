"use client";

import Link from "next/link";

import { useProfileQuery } from "@/api/hooks";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { useAuth } from "@/lib/auth/useAuth";

function ProfileContent() {
  const { user } = useAuth();
  const {
    data: profile,
    isLoading,
    isError,
  } = useProfileQuery(user?.id ?? 0);

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size="lg" />
      </div>
    );
  }

  const hasProfile = !isError && !!profile;

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8 flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Мой профиль</h1>
        <Link href="/profile/edit" className="btn-secondary">
          {hasProfile ? "Редактировать" : "Создать профиль"}
        </Link>
      </div>

      <div className="card">
        <div className="mb-6 flex items-center gap-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-brand-100 text-xl font-bold text-brand-600">
            {user?.username[0]?.toUpperCase()}
          </div>
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              {profile?.display_name ?? user?.username}
            </h2>
            <p className="text-sm text-gray-500">{user?.email}</p>
          </div>
        </div>

        {hasProfile ? (
          <div className="space-y-4">
            {profile.specialization && (
              <div>
                <h3 className="label">Специализация</h3>
                <p className="text-gray-700">{profile.specialization}</p>
              </div>
            )}
            {profile.bio && (
              <div>
                <h3 className="label">О себе</h3>
                <p className="whitespace-pre-wrap text-gray-700">{profile.bio}</p>
              </div>
            )}
            {profile.skills.length > 0 && (
              <div>
                <h3 className="label mb-1">Навыки</h3>
                <div className="flex flex-wrap gap-1.5">
                  {profile.skills.map((skill) => (
                    <Badge key={skill} variant="info">{skill}</Badge>
                  ))}
                </div>
              </div>
            )}
            {profile.contacts.length > 0 && (
              <div>
                <h3 className="label mb-1">Контакты</h3>
                <ul className="space-y-1">
                  {profile.contacts.map((c) => (
                    <li key={`${c.provider}-${c.contact}`} className="text-sm text-gray-700">
                      <span className="font-medium">{c.provider}:</span> {c.contact}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ) : (
          <div className="py-8 text-center">
            <p className="text-gray-500">Профиль ещё не создан</p>
            <Link href="/profile/edit" className="btn-primary mt-4 inline-block">
              Создать профиль
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}

export default function ProfilePage() {
  return (
    <ProtectedRoute>
      <ProfileContent />
    </ProtectedRoute>
  );
}
