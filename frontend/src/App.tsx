import { Navigate, Route, Routes } from 'react-router';
import './App.css';
import { ApiProvider } from './app/api-provider';
import { HomePage } from './pages/home-page';

const App = () => {
  return (
    <ApiProvider>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="*" element={<Navigate replace to="/" />} />
      </Routes>
    </ApiProvider>
  );
};

export default App;
