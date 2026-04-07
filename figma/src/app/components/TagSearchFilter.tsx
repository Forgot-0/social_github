import { useMemo, useState } from "react";
import { Plus, X } from "lucide-react";
import { Checkbox } from "./ui/checkbox";

export const POPULAR_TECH_TAGS = ["Python", "JavaScript", "TypeScript", "Go", "ML"];

export function normalizeFilterValue(value: string) {
  return value.trim().toLowerCase();
}

function uniqueTags(tags: string[]) {
  const seen = new Set<string>();
  const result: string[] = [];

  for (const tag of tags) {
    const trimmed = tag.trim();
    if (!trimmed) continue;
    const key = normalizeFilterValue(trimmed);
    if (seen.has(key)) continue;
    seen.add(key);
    result.push(trimmed);
  }

  return result;
}

function hasTag(tags: string[], tag: string) {
  const normalized = normalizeFilterValue(tag);
  return tags.some((item) => normalizeFilterValue(item) === normalized);
}

interface TagSearchFilterProps {
  selectedTags: string[];
  onChange: (tags: string[]) => void;
  placeholder?: string;
  title?: string;
  subtitle?: string;
  frequentTags?: string[];
  availableTags?: string[];
}

export function TagSearchFilter({
  selectedTags,
  onChange,
  placeholder = "Введите тег и нажмите Enter",
  title = "Теги",
  subtitle,
  frequentTags = POPULAR_TECH_TAGS,
  availableTags = [],
}: TagSearchFilterProps) {
  const [inputValue, setInputValue] = useState("");

  const options = useMemo(
    () => uniqueTags([...frequentTags, ...availableTags]),
    [frequentTags, availableTags],
  );

  const addTag = (rawValue: string) => {
    const trimmed = rawValue.trim();
    if (!trimmed || hasTag(selectedTags, trimmed)) {
      setInputValue("");
      return;
    }

    onChange([...selectedTags, trimmed]);
    setInputValue("");
  };

  const removeTag = (tagToRemove: string) => {
    onChange(selectedTags.filter((tag) => normalizeFilterValue(tag) !== normalizeFilterValue(tagToRemove)));
  };

  const toggleTag = (tag: string) => {
    if (hasTag(selectedTags, tag)) {
      removeTag(tag);
      return;
    }
    onChange([...selectedTags, tag]);
  };

  return (
    <div className="space-y-3 rounded-2xl border border-border bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-foreground">{title}</h3>
          {subtitle ? <p className="mt-1 text-xs text-muted-foreground sm:text-sm">{subtitle}</p> : null}
        </div>
        {selectedTags.length > 0 ? (
          <button type="button" onClick={() => onChange([])} className="text-xs font-medium text-primary hover:underline sm:text-sm">
            Сбросить
          </button>
        ) : null}
      </div>

      <div className="flex flex-col gap-2 sm:flex-row">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              addTag(inputValue);
            }
          }}
          placeholder={placeholder}
          className="app-input flex-1"
        />
        <button
          type="button"
          onClick={() => addTag(inputValue)}
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-primary px-4 py-3 text-white transition-colors hover:bg-accent"
        >
          <Plus className="h-4 w-4" />
          <span>Добавить</span>
        </button>
      </div>

      <div className="flex flex-wrap gap-2">
        {options.map((tag) => {
          const checked = hasTag(selectedTags, tag);
          return (
            <label
              key={tag}
              className={`inline-flex cursor-pointer items-center gap-1.5 rounded-full border px-2.5 py-1.5 text-[11px] font-medium transition-all sm:text-xs ${
                checked
                  ? "border-primary bg-primary/8 text-primary shadow-sm"
                  : "border-border bg-secondary/35 text-foreground hover:border-primary/30 hover:bg-secondary/70"
              }`}
            >
              <Checkbox
                checked={checked}
                onCheckedChange={() => toggleTag(tag)}
                aria-label={`Выбрать тег ${tag}`}
                className="size-3 rounded-[3px]"
              />
              <span>{tag}</span>
            </label>
          );
        })}
      </div>

      {selectedTags.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {selectedTags.map((tag) => (
            <span key={tag} className="inline-flex items-center gap-1.5 rounded-full bg-primary px-3 py-1 text-[11px] text-white shadow-sm sm:text-xs">
              <span>{tag}</span>
              <button type="button" onClick={() => removeTag(tag)} className="rounded-full p-0.5 hover:bg-white/15" aria-label={`Удалить тег ${tag}`}>
                <X className="h-3.5 w-3.5" />
              </button>
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}
