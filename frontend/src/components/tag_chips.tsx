type TagChipsProps = {
  items: string[];
  emptyText?: string;
  containerClassName?: string;
  chipClassName?: string;
};

export function TagChips({
  items,
  emptyText = 'Теги не указаны',
  containerClassName = 'flex flex-wrap gap-2',
  chipClassName = 'rounded-full border border-zinc-700 bg-zinc-800 px-3 py-1 text-xs font-medium text-zinc-100 transition hover:border-zinc-500 hover:bg-zinc-700',
}: TagChipsProps) {
  if (!items.length) {
    return <p className="text-xs text-zinc-500">{emptyText}</p>;
  }

  return (
    <div className={containerClassName}>
      {items.map((item) => (
        <span key={item} className={chipClassName}>
          {item}
        </span>
      ))}
    </div>
  );
}
