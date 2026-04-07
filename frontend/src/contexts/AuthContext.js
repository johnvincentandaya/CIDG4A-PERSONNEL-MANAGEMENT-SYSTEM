import React, { createContext, useState, useEffect } from 'react';
import { APP_PASSWORD } from '../config/authConfig';

export const AuthContext = createContext({ loggedIn: false, login: async ()=>{}, logout: ()=>{} });

export function AuthProvider({ children }){
  const [loggedIn, setLoggedIn] = useState(() => {
    try{
      // sessionStorage persists until browser/tab is closed
      const v = sessionStorage.getItem('cidg_logged_in');
      return v === '1';
    }catch(e){ return false; }
  });

  useEffect(()=>{
    try{ sessionStorage.setItem('cidg_logged_in', loggedIn ? '1' : '0'); }catch(e){}
  },[loggedIn]);

  async function login(password){
    // strict exact match, case-sensitive
    if (password === APP_PASSWORD){
      setLoggedIn(true);
      return { ok: true };
    }
    return { ok: false, message: 'Invalid password' };
  }

  function logout(){
    setLoggedIn(false);
    try{ sessionStorage.removeItem('cidg_logged_in'); }catch(e){}
  }

  return (
    <AuthContext.Provider value={{ loggedIn, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
