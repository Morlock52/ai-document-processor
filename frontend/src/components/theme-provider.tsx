'use client';

import React from 'react';
import { ThemeContext, useThemeProvider } from '@/hooks/use-theme';

interface ThemeProviderProps {
  children: React.ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  const value = useThemeProvider();

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}