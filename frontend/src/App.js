import React from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import Form201 from './components/Form201';
import BMIMonitor from './components/BMIMonitor';
import Login from './components/Login';
import { useContext } from 'react';
import { AuthContext } from './contexts/AuthContext';
import ThemeToggle from './components/ThemeToggle';

function App() {
  const { loggedIn } = useContext(AuthContext);
  return (
    <BrowserRouter>
      <div className="app-shell">
        {loggedIn ? <Sidebar /> : null}
        <div className="app-main">
          <div className="app-topbar d-flex justify-content-end p-2">
            <ThemeToggle />
          </div>
          <Routes>
            <Route path="/" element={loggedIn ? <Navigate to="/dashboard" replace /> : <Navigate to="/login" replace />} />
            <Route path="/login" element={<Login />} />
            <Route path="/dashboard" element={loggedIn ? <Dashboard /> : <Navigate to="/login" replace />} />
            <Route path="/form201" element={loggedIn ? <Form201 /> : <Navigate to="/login" replace />} />
            <Route path="/bmi" element={loggedIn ? <BMIMonitor /> : <Navigate to="/login" replace />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
