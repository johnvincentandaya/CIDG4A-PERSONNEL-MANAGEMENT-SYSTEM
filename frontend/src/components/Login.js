import React, { useState, useContext, useEffect } from 'react';
import cidgLogo from '../assets/cidg-logo.png';
import { AuthContext } from '../contexts/AuthContext';
import { ThemeContext } from '../contexts/ThemeContext';
import { useNavigate } from 'react-router-dom';

export default function Login(){
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login, loggedIn } = useContext(AuthContext);
  const { theme } = useContext(ThemeContext);
  const navigate = useNavigate();

  useEffect(()=>{ if (loggedIn) navigate('/dashboard'); },[loggedIn,navigate]);

  async function doLogin(e){
    e.preventDefault();
    setError('');
    const res = await login(password);
    if (res.ok){
      navigate('/dashboard');
    } else {
      setError('Incorrect password. Please try again.');
    }
  }

  return (
    <div className={`login-page d-flex align-items-center justify-content-center vh-100`}>
      <div className="card p-4" style={{width:360}}>
        <div className="text-center mb-3">
          <img src={cidgLogo} alt="CIDG logo" style={{height:64}} />
          <h5 className="mt-2">CIDG RFU4A Personnel Management System</h5>
        </div>
        <form onSubmit={doLogin}>
          <div className="mb-3">
            <label className="form-label">Password</label>
            <input type="password" className="form-control" value={password} onChange={e=>setPassword(e.target.value)} autoFocus />
          </div>
          {error && <div className="alert alert-danger small">{error}</div>}
          <div className="d-grid">
            <button className="btn btn-primary" type="submit">Login</button>
          </div>
        </form>
      </div>
    </div>
  );
}
