import React from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import Form201 from './components/Form201';
import BMIMonitor from './components/BMIMonitor';
import ChangePassword from './components/ChangePassword';
import Login from './components/Login';
import { useContext } from 'react';
import { AuthContext } from './contexts/AuthContext';
import ThemeToggle from './components/ThemeToggle';

// Protected Route Component
function ProtectedRoute({ children }) {
  const { loggedIn, authReady } = useContext(AuthContext);

  if (!authReady) return null;
  return loggedIn ? children : <Navigate to="/login" replace />;
}

function App() {
  const { loggedIn, authReady } = useContext(AuthContext);
  return (
    <BrowserRouter>
      <div className="app-shell">
        {loggedIn ? <Sidebar /> : null}
        <div className="app-main">
          <div className="app-topbar d-flex justify-content-end p-2">
            {loggedIn && <ThemeToggle />}
          </div>
          <Routes>
            <Route
              path="/"
              element={
                !authReady
                  ? null
                  : (loggedIn ? <Navigate to="/dashboard" replace /> : <Navigate to="/login" replace />)
              }
            />
            <Route path="/login" element={<Login />} />
            <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/form201" element={<ProtectedRoute><Form201 /></ProtectedRoute>} />
            <Route path="/bmi" element={<ProtectedRoute><BMIMonitor /></ProtectedRoute>} />
            <Route path="/change-password" element={<ProtectedRoute><ChangePassword /></ProtectedRoute>} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
