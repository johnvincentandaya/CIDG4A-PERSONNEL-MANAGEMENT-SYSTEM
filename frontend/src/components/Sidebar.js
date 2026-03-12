import React from 'react';
import { NavLink } from 'react-router-dom';
import cidgLogo from '../assets/cidg-logo.png';

export default function Sidebar(){
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo-wrap">
          <img
            src={cidgLogo}
            alt="CIDG logo"
            className="sidebar-logo"
          />
        </div>
        <div>
          <div className="sidebar-agency">CIDG RFU4A</div>
          <div className="sidebar-subtitle">Personnel Management System</div>
        </div>
      </div>

      <div className="sidebar-nav-label">Navigation</div>
      <nav className="sidebar-nav">
        <NavLink
          to="/dashboard"
          className={({ isActive }) =>
            'sidebar-nav-link' + (isActive ? ' active' : '')
          }
        >
          <i className="bi bi-speedometer2" />
          <span>Dashboard</span>
        </NavLink>
        <NavLink
          to="/form201"
          className={({ isActive }) =>
            'sidebar-nav-link' + (isActive ? ' active' : '')
          }
        >
          <i className="bi bi-folder2-open" />
          <span>Form 201 Records</span>
        </NavLink>
        <NavLink
          to="/bmi"
          className={({ isActive }) =>
            'sidebar-nav-link' + (isActive ? ' active' : '')
          }
        >
          <i className="bi bi-activity" />
          <span>BMI Monitoring</span>
        </NavLink>
      </nav>

      <div className="sidebar-footer">
        © {new Date().getFullYear()} CIDG RFU4A
      </div>
    </aside>
  )
}
