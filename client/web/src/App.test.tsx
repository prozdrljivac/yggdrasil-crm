import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { App } from './App';

describe('local development shell', () => {
  it('shows progress while the API request is pending', () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => new Promise(() => {})),
    );
    render(<App />);
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      'YggdrasilCRM',
    );
    expect(screen.getByRole('status')).toHaveTextContent('Checking');
  });

  it('reports a healthy API', async () => {
    const fetch = vi.fn().mockResolvedValue(Response.json({ status: 'ok' }));
    vi.stubGlobal('fetch', fetch);
    render(<App />);
    expect(await screen.findByText('Local API is running.')).toBeVisible();
    expect(fetch).toHaveBeenCalledWith('/api/health', {
      signal: expect.any(AbortSignal),
    });
  });

  it.each([
    () => Promise.reject(new Error('Connection refused')),
    () => Promise.resolve(new Response(null, { status: 503 })),
    () => Promise.resolve(Response.json({ status: 'unexpected' })),
  ])(
    'reports an unavailable API without showing internal errors',
    async (fetch) => {
      vi.stubGlobal('fetch', vi.fn(fetch));
      render(<App />);
      expect(await screen.findByText(/Local API is unavailable/)).toBeVisible();
      expect(screen.queryByText(/Connection refused/)).not.toBeInTheDocument();
    },
  );

  it('aborts the API request when unmounted', () => {
    const fetch = vi
      .fn<typeof globalThis.fetch>()
      .mockImplementation(() => new Promise(() => {}));
    vi.stubGlobal('fetch', fetch);
    const { unmount } = render(<App />);
    const signal = fetch.mock.calls[0]?.[1]?.signal;
    expect(signal).toBeInstanceOf(AbortSignal);
    unmount();
    expect(signal?.aborted).toBe(true);
  });
});
