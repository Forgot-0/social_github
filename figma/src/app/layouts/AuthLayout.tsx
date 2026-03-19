import { Outlet } from 'react-router';
import { Toaster } from '../components/ui/sonner';

export function AuthLayout() {
  return (
    <>
      <Outlet />
      <Toaster />
    </>
  );
}
