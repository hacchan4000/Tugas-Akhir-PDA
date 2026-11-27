import { useContext } from 'react';
import { HistContext } from '@/context/HistContext';

export const useHist = () => useContext(HistContext);
