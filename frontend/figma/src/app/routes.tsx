import { createBrowserRouter } from 'react-router';
import { RootLayout } from './layouts/RootLayout';
import { AuthLayout } from './layouts/AuthLayout';
import { ProtectedRoute } from './components/ProtectedRoute';
import { HomePage } from './pages/HomePage';
import { ProjectDetailPage } from './pages/ProjectDetailPage';
import { CreateProjectPage } from './pages/CreateProjectPage';
import { MyProjectsPage } from './pages/MyProjectsPage';
import { ProfilePage } from './pages/ProfilePage';
import { UserProfilePage } from './pages/UserProfilePage';
import { SettingsPage } from './pages/SettingsPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { NotFoundPage } from './pages/NotFoundPage';

export const router = createBrowserRouter([
  {
    path: '/auth',
    Component: AuthLayout,
    children: [
      { path: 'login', Component: LoginPage },
      { path: 'register', Component: RegisterPage },
    ],
  },
  {
    path: '/',
    Component: RootLayout,
    children: [
      { index: true, Component: HomePage },
      { path: 'projects/:id', Component: ProjectDetailPage },
      { 
        path: 'create-project', 
        element: <ProtectedRoute><CreateProjectPage /></ProtectedRoute>
      },
      { 
        path: 'my-projects', 
        element: <ProtectedRoute><MyProjectsPage /></ProtectedRoute>
      },
      { 
        path: 'profile', 
        element: <ProtectedRoute><ProfilePage /></ProtectedRoute>
      },
      { 
        path: 'users/:id', 
        Component: UserProfilePage
      },
      { 
        path: 'settings', 
        element: <ProtectedRoute><SettingsPage /></ProtectedRoute>
      },
      { path: '*', Component: NotFoundPage },
    ],
  },
]);