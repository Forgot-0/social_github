import { useState } from 'react';

type TagEditorProps = {
  label: string;
  values: string[];
  onChange: (next: string[]) => void;
  placeholder?: string;
  helperText?: string;
};

export function TagEditor({
  label,
  values,
  onChange,
  placeholder = 'Добавить тег...',
  helperText = 'Enter или запятая — добавить тег',
}: TagEditorProps) {
  const [draft, setDraft] = useState('');

  const normalize = (value: string) => value.trim().replace(/\s+/g, ' ');

  const addTag = () => {
    const nextTag = normalize(draft);
    if (!nextTag) return;

    const exists = values.some(
      (tag) => tag.toLowerCase() === nextTag.toLowerCase(),
    );
    if (exists) {
      setDraft('');
      return;
    }

    onChange([...values, nextTag]);
    setDraft('');
  };

  const removeTag = (tagToRemove: string) => {
    onChange(values.filter((tag) => tag !== tagToRemove));
  };

  return (
    <div className="md:col-span-2">
      <label className="text-sm text-zinc-300">{label}</label>

      <div className="mt-1 rounded-2xl border border-zinc-700 bg-zinc-950 px-3 py-3">
        <div className="flex flex-wrap gap-2">
          {values.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center gap-2 rounded-full border border-zinc-700 bg-zinc-900 px-3 py-1 text-sm text-zinc-100 transition hover:border-zinc-500 hover:bg-zinc-800"
            >
              {tag}
              <button
                type="button"
                onClick={() => removeTag(tag)}
                className="text-zinc-400 hover:text-white"
                aria-label={`Удалить тег ${tag}`}
              >
                ×
              </button>
            </span>
          ))}

          <input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ',') {
                e.preventDefault();
                addTag();
              }
              if (e.key === 'Backspace' && !draft && values.length) {
                removeTag(values[values.length - 1]);
              }
            }}
            onBlur={addTag}
            placeholder={placeholder}
            className="min-w-[180px] flex-1 bg-transparent px-1 py-1 text-zinc-100 outline-none placeholder:text-zinc-500"
          />
        </div>

        <p className="mt-2 text-xs text-zinc-500">{helperText}</p>
      </div>
    </div>
  );
}
