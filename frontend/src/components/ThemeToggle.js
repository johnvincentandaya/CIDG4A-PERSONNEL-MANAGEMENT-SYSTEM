import React, { useContext } from 'react';
import { ThemeContext } from '../contexts/ThemeContext';

export default function ThemeToggle(){
  const { theme, toggle } = useContext(ThemeContext);
  return (
    <button className="btn btn-sm btn-outline-secondary" onClick={toggle} aria-label="Toggle theme" title="Toggle theme">
      {theme === 'dark' ? <i className="bi bi-sun-fill" /> : <i className="bi bi-moon-fill" />}
    </button>
  );
}
