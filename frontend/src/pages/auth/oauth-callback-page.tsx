import { useEffect, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router';
import { useAuth } from '../../features/auth/auth-context.tsx';
import { isApiError } from '../../features/auth/api-error.ts';
import {
  OAUTH_PROVIDERS,
  type OAuthProvider,
} from '../../features/auth/oauth-providers.ts';

function isOAuthProvider(p: string | undefined): p is OAuthProvider {
  return p !== undefined && OAUTH_PROVIDERS.includes(p as OAuthProvider);
}

export function OAuthCallbackPage() {
  const { provider: providerParam } = useParams<{ provider: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { completeOAuthLogin } = useAuth();
  const [message, setMessage] = useState('Завершение входа…');
  const code = searchParams.get('code');
  const state = searchParams.get('state');
  useEffect(() => {
    if (!isOAuthProvider(providerParam)) {
      setMessage('Неизвестный провайдер OAuth');
      return;
    }
    if (!code || !state) {
      setMessage('Нет параметров code или state');
      return;
    }

    let cancelled = false;
    (async () => {
      try {
        await completeOAuthLogin(providerParam, { code, state });
        if (!cancelled) navigate('/', { replace: true });
      } catch (err) {
        if (!cancelled) {
          setMessage(
            isApiError(err) ? err.message : 'Ошибка OAuth. Попробуйте снова.',
          );
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [code, completeOAuthLogin, navigate, providerParam, state]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-950 px-4">
      <div className="max-w-md rounded-xl border border-zinc-800 bg-zinc-900/80 px-6 py-8 text-center text-zinc-200">
        <p>{message}</p>
        {message !== 'Завершение входа…' ? (
          <button
            type="button"
            onClick={() => navigate('/login', { replace: true })}
            className="mt-6 rounded-lg border border-zinc-600 px-4 py-2 text-sm hover:bg-zinc-800"
          >
            На страницу входа
          </button>
        ) : null}
      </div>
    </div>
  );
}
