import { createBrowserRouter } from 'react-router-dom';
import { Layout } from './components/Layout';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Home } from './pages/Home';
import { Projects } from './pages/Projects';
import { People } from './pages/People';
import { CreateProject } from './pages/CreateProject';
import { ProjectDetail } from './pages/ProjectDetail';
import { Positions } from './pages/Positions';
import { Applications } from './pages/Applications';
import { MyProjects } from './pages/MyProjects';
import { Profile } from './pages/Profile';
import { Chat } from './pages/Chat';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { NotFound } from './pages/NotFound';

export const router = createBrowserRouter([
  {
    path: '/',
    Component: Layout,
    children: [
      { index: true, Component: Home },
      { path: 'projects', Component: Projects },
      { path: 'people', Component: People },
      {
        path: 'projects/create',
        element: (
          <ProtectedRoute>
            <CreateProject />
          </ProtectedRoute>
        ),
      },
      { path: 'projects/:id', Component: ProjectDetail },
      { path: 'positions', Component: Positions },
      {
        path: 'applications',
        element: (
          <ProtectedRoute>
            <Applications />
          </ProtectedRoute>
        ),
      },
      {
        path: 'my-projects',
        element: (
          <ProtectedRoute>
            <MyProjects />
          </ProtectedRoute>
        ),
      },
      {
        path: 'profile',
        element: (
          <ProtectedRoute>
            <Profile />
          </ProtectedRoute>
        ),
      },
      { path: 'profiles/:id', Component: Profile },
      {
        path: 'chat',
        element: (
          <ProtectedRoute>
            <Chat />
          </ProtectedRoute>
        ),
      },
      { path: '*', Component: NotFound },
    ],
  },
  {
    path: '/login',
    Component: Login,
  },
  {
    path: '/register',
    Component: Register,
  },
]);
