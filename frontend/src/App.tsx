import { Route, Routes } from 'react-router';
import './App.css';
import { LoginPage } from './pages/auth/login-page.tsx';
import { OAuthCallbackPage } from './pages/auth/oauth-callback-page.tsx';
import { RegisterPage } from './pages/auth/register-page.tsx';
import { HomePage } from './pages/home-page.tsx';

const App = () => {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/auth/callback/:provider" element={<OAuthCallbackPage />} />
    </Routes>
  );
};

export default App;
