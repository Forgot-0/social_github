import { Navigate, Route, Routes } from 'react-router';
import './App.css';
import { LoginPage } from './pages/auth/login-page.tsx';
import { OAuthCallbackPage } from './pages/auth/oauth-callback-page.tsx';
import { RegisterPage } from './pages/auth/register-page.tsx';
import { HomePage } from './pages/home-page.tsx';
import { ProfilePage } from './pages/profile-page.tsx';
import { AuthenticatedLayout } from './layouts/authenticated-layout.tsx';

const App = () => {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/auth/callback/:provider" element={<OAuthCallbackPage />} />
      <Route element={<AuthenticatedLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/profile" element={<ProfilePage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default App;
