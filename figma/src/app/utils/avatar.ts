import type { AvatarFormats } from '../../api/types';

/**
 * Размеры аватаров, доступные в системе
 */
export type AvatarSize = '32' | '64' | '256' | '512';

/**
 * Форматы изображений в порядке приоритета (современные форматы первыми)
 */
const FORMAT_PRIORITY: (keyof AvatarFormats)[] = ['webp', 'avif', 'jpg'];

/**
 * Размеры в порядке приоритета для fallback
 */
const SIZE_PRIORITY: AvatarSize[] = ['256', '64', '512', '32'];

/**
 * Получает URL аватара из объекта avatars профиля
 * 
 * @param avatars - Объект с аватарами из ProfileDTO
 * @param preferredSize - Предпочитаемый размер (по умолчанию '64')
 * @returns URL аватара или undefined если аватар отсутствует
 */
export function getAvatarUrl(
  avatars: Record<string, AvatarFormats> | null | undefined,
  preferredSize: AvatarSize = '64'
): string | undefined {
  if (!avatars || Object.keys(avatars).length === 0) {
    return undefined;
  }

  // Попытка получить предпочитаемый размер
  const preferredSizeData = avatars[preferredSize];
  if (preferredSizeData) {
    // Ищем перв��й доступный формат по приоритету
    for (const format of FORMAT_PRIORITY) {
      if (preferredSizeData[format]) {
        return preferredSizeData[format];
      }
    }
  }

  // Fallback: ищем любой доступный размер в порядке приоритета
  for (const size of SIZE_PRIORITY) {
    const sizeData = avatars[size];
    if (sizeData) {
      for (const format of FORMAT_PRIORITY) {
        if (sizeData[format]) {
          return sizeData[format];
        }
      }
    }
  }

  return undefined;
}
