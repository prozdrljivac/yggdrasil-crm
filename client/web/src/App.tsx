import { useEffect, useState } from 'react';

type ApiState = 'loading' | 'ready' | 'unavailable';

async function checkApi(signal: AbortSignal): Promise<void> {
  const response = await fetch('/api/health', { signal });
  if (!response.ok) throw new Error('API health check failed');

  const body: unknown = await response.json();
  if (
    typeof body !== 'object' ||
    body === null ||
    !('status' in body) ||
    body.status !== 'ok'
  ) {
    throw new Error('Invalid API health response');
  }
}

const messages: Record<ApiState, string> = {
  loading: 'Checking the local API…',
  ready: 'Local API is running.',
  unavailable:
    'Local API is unavailable. Start the API, then reload this page.',
};

export function App() {
  const [apiState, setApiState] = useState<ApiState>('loading');

  useEffect(() => {
    const controller = new AbortController();
    void checkApi(controller.signal).then(
      () => {
        if (!controller.signal.aborted) setApiState('ready');
      },
      () => {
        if (!controller.signal.aborted) setApiState('unavailable');
      },
    );
    return () => controller.abort();
  }, []);

  return (
    <main>
      <h1>YggdrasilCRM</h1>
      <p>Local development shell. No business records are loaded.</p>
      <p role="status">{messages[apiState]}</p>
    </main>
  );
}
