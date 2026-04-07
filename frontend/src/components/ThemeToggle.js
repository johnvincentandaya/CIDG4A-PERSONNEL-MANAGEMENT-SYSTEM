import React, { useContext } from 'react';
import { ThemeContext } from '../contexts/ThemeContext';

export default function ThemeToggle(){
  const { theme, toggle } = useContext(ThemeContext);
  return (
    <div className="theme-toggle d-flex align-items-center gap-2">
      <button className="btn btn-sm btn-outline-secondary" onClick={toggle} aria-label="Toggle theme">{theme === 'dark' ? 'Dark' : 'Light'}</button>
    </div>
  );
}
