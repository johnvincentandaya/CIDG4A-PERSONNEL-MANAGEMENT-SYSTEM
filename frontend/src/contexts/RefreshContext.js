import React, { createContext, useState } from 'react';

export const RefreshContext = createContext({ version: 0, bump: () => {} });

export function RefreshProvider({ children }){
  const [version, setVersion] = useState(0);
  function bump(){ setVersion(v => v + 1); }
  return (
    <RefreshContext.Provider value={{ version, bump }}>
      {children}
    </RefreshContext.Provider>
  );
}
