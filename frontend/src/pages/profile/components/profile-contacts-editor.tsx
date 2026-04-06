import type { ContactDTO } from '../../../types/api/profile.ts';

export type ContactProvider = 'telegram' | 'github' | 'email';

type ProfileContactsEditorProps = {
  providers: ContactProvider[];
  provider: ContactProvider;
  value: string;
  contacts: ContactDTO[];
  isPending: boolean;
  message: string | null;
  validationError: string | null;
  onProviderChange: (provider: ContactProvider) => void;
  onValueChange: (value: string) => void;
  onAdd: () => void;
  onDelete: (provider: string) => void;
};

export function ProfileContactsEditor({
  providers,
  provider,
  value,
  contacts,
  isPending,
  message,
  validationError,
  onProviderChange,
  onValueChange,
  onAdd,
  onDelete,
}: ProfileContactsEditorProps) {
  return (
    <div className="md:col-span-2 border-t border-zinc-800 pt-4">
      <h3 className="text-sm font-medium text-zinc-200">Контакты</h3>
      <p className="mt-1 text-xs text-zinc-500">
        Telegram, GitHub и Email для связи.
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        <select
          value={provider}
          onChange={(event) =>
            onProviderChange(event.target.value as ContactProvider)
          }
          className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-200"
        >
          {providers.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
        <input
          value={value}
          onChange={(event) => onValueChange(event.target.value)}
          placeholder="Введите контакт"
          className="min-w-[220px] flex-1 rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-zinc-100"
        />
        <button
          type="button"
          onClick={onAdd}
          disabled={isPending}
          className="rounded-lg border border-zinc-700 px-3 py-2 text-sm text-zinc-200 hover:bg-zinc-800 disabled:opacity-50"
        >
          Добавить
        </button>
      </div>

      {validationError ? (
        <p className="mt-2 text-xs text-red-300">{validationError}</p>
      ) : null}

      <div className="mt-3 space-y-2">
        {contacts.length ? (
          contacts.map((contact) => (
            <div
              key={`${contact.provider}-${contact.contact}`}
              className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm"
            >
              <span className="text-zinc-300">
                <span className="text-zinc-500">{contact.provider}:</span>{' '}
                {contact.contact}
              </span>
              <button
                type="button"
                onClick={() => onDelete(contact.provider)}
                disabled={isPending}
                className="text-xs text-red-300 hover:text-red-200 disabled:opacity-50"
              >
                Удалить
              </button>
            </div>
          ))
        ) : (
          <p className="text-xs text-zinc-500">Контакты не добавлены.</p>
        )}
      </div>

      {message ? <p className="mt-2 text-sm text-zinc-400">{message}</p> : null}
    </div>
  );
}
