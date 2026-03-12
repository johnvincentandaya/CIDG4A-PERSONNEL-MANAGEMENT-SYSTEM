import React from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import Form201 from './components/Form201';
import BMIMonitor from './components/BMIMonitor';

function App() {
  return (
    <BrowserRouter>
      <div className="d-flex" style={{minHeight:'100vh'}}>
        <Sidebar />
        <div className="flex-grow-1 p-4 bg-light">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/form201" element={<Form201 />} />
            <Route path="/bmi" element={<BMIMonitor />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
