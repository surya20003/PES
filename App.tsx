import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Login from './components/Login';
import RoomList from './components/RoomList';
import HomePage from './components/HomePage';
import Layout from './components/Layout';
import NotFoundPage from './components/NotFoundPage';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

const AppContent: React.FC = () => {
  const { isAuthenticated, user, logout } = useAuth();

  if (!isAuthenticated) {
    return <Login />;
  }

  return (
    <Layout title="AI Chat App" user={user || undefined} onLogout={logout}>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/rooms" element={<RoomList onLogout={logout} username={user?.username || ''} />} />
        <Route path="*" element={<NotFoundPage onBack={() => window.history.back()} />} />
      </Routes>
    </Layout>
  );
};

const App: React.FC = () => {
  return (
    <Router>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AuthProvider>
          <AppContent />
        </AuthProvider>
      </ThemeProvider>
    </Router>
  );
};

export default App;
