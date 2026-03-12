import React from 'react';
import { NavLink } from 'react-router-dom';

export default function Sidebar(){
  return (
    <div style={{width:260,background:'#163b8f',color:'#fff',minHeight:'100vh'}} className="d-flex flex-column p-3">
      <div className="mb-4">
        <div className="rounded bg-white d-inline-block p-2" style={{color:'#163b8f'}}>CIDG</div>
        <div className="mt-2">CRIMINAL INVESTIGATION AND DETECTION GROUP</div>
      </div>
      <nav className="nav nav-pills flex-column">
        <NavLink to="/dashboard" className="nav-link text-white mb-2" style={{background:'transparent'}} activeclassname="active">Dashboard</NavLink>
        <NavLink to="/form201" className="nav-link text-white mb-2">Form 201</NavLink>
        <NavLink to="/bmi" className="nav-link text-white mb-2">BMI Monitoring</NavLink>
        
      </nav>
      <div className="mt-auto small">© 2026 CIDG RFU4A</div>
    </div>
  )
}
