import { useMemo, type ReactNode } from 'react';
import { createApiServices } from '../services';
import { ApiContext } from './api-context';
import { appEnv } from './env';

export interface ApiProviderProps {
  readonly children: ReactNode;
}

export const ApiProvider = ({ children }: ApiProviderProps) => {
  const services = useMemo(
    () =>
      createApiServices({
        basePath: appEnv.apiBaseUrl,
      }),
    [],
  );

  return <ApiContext.Provider value={services}>{children}</ApiContext.Provider>;
};
