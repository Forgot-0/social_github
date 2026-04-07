import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { cn } from "./ui/utils";

export interface StyledSelectOption {
  value: string | number;
  label: string;
}

interface StyledSelectProps {
  value?: string | number | null;
  onChange: (value: string) => void;
  options: StyledSelectOption[];
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  triggerClassName?: string;
  contentClassName?: string;
}

export function StyledSelect({
  value,
  onChange,
  options,
  placeholder = "Выберите значение",
  disabled = false,
  className,
  triggerClassName,
  contentClassName,
}: StyledSelectProps) {
  const normalizedValue = value === undefined || value === null ? undefined : String(value);

  return (
    <div className={className}>
      <Select value={normalizedValue} onValueChange={onChange} disabled={disabled}>
        <SelectTrigger
          className={cn(
            "h-11 w-full rounded-2xl border border-border bg-white px-4 text-sm font-medium text-foreground shadow-sm transition-all hover:border-primary/30 focus:border-primary focus:ring-4 focus:ring-primary/10 data-[placeholder]:text-muted-foreground",
            triggerClassName,
          )}
        >
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent
          className={cn(
            "rounded-2xl border border-border bg-white p-1.5 shadow-xl shadow-slate-900/8",
            contentClassName,
          )}
        >
          {options.map((option) => (
            <SelectItem
              key={String(option.value)}
              value={String(option.value)}
              className="rounded-xl px-3 py-2.5 text-sm font-medium text-foreground focus:bg-primary/8 focus:text-foreground"
            >
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
