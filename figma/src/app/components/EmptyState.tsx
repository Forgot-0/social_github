import { LucideIcon } from "lucide-react";
import { ReactNode } from "react";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description?: string;
  action?: ReactNode;
}

export function EmptyState({ icon: Icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="text-center py-12">
      <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
        <Icon className="w-8 h-8 text-muted-foreground" />
      </div>
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      {description && <p className="text-muted-foreground mb-6">{description}</p>}
      {action && <div>{action}</div>}
    </div>
  );
}

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
}

export function LoadingSpinner({ size = 'md', text }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'h-8 w-8',
    md: 'h-12 w-12',
    lg: 'h-16 w-16',
  };

  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div className={`inline-block animate-spin rounded-full border-b-2 border-primary ${sizeClasses[size]}`} />
      {text && <p className="mt-4 text-muted-foreground">{text}</p>}
    </div>
  );
}

interface ErrorMessageProps {
  title?: string;
  message: string;
  retry?: () => void;
}

export function ErrorMessage({ title = "Ошибка", message, retry }: ErrorMessageProps) {
  return (
    <div className="text-center py-12">
      <div className="w-16 h-16 bg-destructive/10 rounded-full flex items-center justify-center mx-auto mb-4">
        <span className="text-3xl">⚠️</span>
      </div>
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-muted-foreground mb-6">{message}</p>
      {retry && (
        <button
          onClick={retry}
          className="px-6 py-3 bg-primary text-white rounded-lg hover:bg-accent transition-colors"
        >
          Попробовать снова
        </button>
      )}
    </div>
  );
}
