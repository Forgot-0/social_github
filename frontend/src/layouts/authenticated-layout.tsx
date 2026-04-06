import { Navigate, Outlet } from 'react-router';
import { useAuth } from '../features/auth/auth-context.tsx';
import { Header } from '../components/layout/header.tsx';
import { Footer } from '../components/layout/footer.tsx';

export function AuthenticatedLayout() {
  const { isReady, isAuthenticated } = useAuth();

  if (!isReady) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-zinc-950 text-zinc-400">
        Загрузка…
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <Header />
      <main className="mx-auto w-full max-w-5xl px-4 py-8">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}
