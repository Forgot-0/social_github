import { createContext, useContext } from 'react';
import type { ApiServices } from '../services';

export const ApiContext = createContext<ApiServices | null>(null);

export function useApi(): ApiServices {
  const value = useContext(ApiContext);
  if (!value) {
    throw new Error('useApi must be used within ApiProvider');
  }
  return value;
}
