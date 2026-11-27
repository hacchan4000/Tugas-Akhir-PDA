'use client';

import React from 'react';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { Toast } from '@/app/components/atoms/toast';
import { AuthProvider } from './AuthContext';
import { HistProvider } from './HistContext';

const muiTheme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#7E1117',
      dark: '#68000B',
      light: '#9F2B2B',
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#26695E',
      dark: '#1D5249',
      light: '#ABECDE',
      contrastText: '#FFFFFF',
    },
    error: {
      main: '#BA1A1A',
    },
    background: {
      default: '#FFF8F7',
      paper: '#FFFFFF',
    },
    text: {
      primary: '#251918',
      secondary: '#58413F',
    },
    divider: '#DFBFBC',
  },
  shape: {
    borderRadius: 12,
  },
  typography: {
    fontFamily: '"Lato", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  },
});

export function AppProvider({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider theme={muiTheme}>
      <LocalizationProvider dateAdapter={AdapterDayjs}>
        <AuthProvider>
          <HistProvider>
            {children}
            <Toast />
          </HistProvider>
        </AuthProvider>
      </LocalizationProvider>
    </ThemeProvider>
  );
}
