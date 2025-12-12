import '@testing-library/jest-dom';
import { afterAll, afterEach, beforeAll } from 'vitest';
import { setupServer } from 'msw/node';
import { HttpResponse, http } from 'msw';

// Mock API handlers
export const handlers = [
  http.get('/api/agents', () => {
    return HttpResponse.json([
      {
        id: '1',
        host_id: 'test-host-1',
        hostname: 'test-server-1',
        os: 'linux',
        architecture: 'x86_64',
        status: 'healthy',
        sampling_interval: 30,
        tags: ['test'],
        modules: {},
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]);
  }),

  http.get('/api/health', () => {
    return HttpResponse.json({ status: 'ok' });
  }),
];

const server = setupServer(...handlers);

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterAll(() => server.close());
afterEach(() => server.resetHandlers());

export { server };
