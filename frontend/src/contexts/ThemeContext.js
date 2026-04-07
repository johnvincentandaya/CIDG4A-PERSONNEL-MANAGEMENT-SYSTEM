import React, { createContext, useState, useEffect } from 'react';

export const ThemeContext = createContext({ theme: 'light', toggle: () => {} });

export function ThemeProvider({ children }){
  const [theme, setTheme] = useState(() => {
    try{
      const saved = localStorage.getItem('cidg_theme');
      return saved || 'light';
    }catch(e){ return 'light'; }
  });

  useEffect(()=>{
    try{ localStorage.setItem('cidg_theme', theme); }catch(e){}
    // apply root attribute
    if (typeof document !== 'undefined'){
      document.documentElement.setAttribute('data-bs-theme', theme === 'dark' ? 'dark' : 'light');
      document.body.classList.toggle('dark', theme === 'dark');
    }
  },[theme]);

  function toggle(){ setTheme(t => t === 'dark' ? 'light' : 'dark'); }

  return (
    <ThemeContext.Provider value={{ theme, toggle }}>
      {children}
    </ThemeContext.Provider>
  );
}
