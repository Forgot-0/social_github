import { Link } from 'react-router-dom';
import logo from '../../assets/logo-incollab.png';

interface AppLogoProps {
  size?: 'sm' | 'md' | 'lg';
  withText?: boolean;
  className?: string;
  to?: string;
}

const sizeMap = {
  sm: 'h-8',
  md: 'h-10',
  lg: 'h-12',
};

export function AppLogo({ size = 'md', withText = false, className = '', to = '/' }: AppLogoProps) {
  return (
    <Link to={to} className={`inline-flex items-center gap-3 min-w-0 ${className}`.trim()}>
      <img src={logo} alt="ИнКоллаб" className={`${sizeMap[size]} w-auto shrink-0`} />
      {withText && <span className="truncate text-xl font-semibold text-foreground">ИнКоллаб</span>}
    </Link>
  );
}
