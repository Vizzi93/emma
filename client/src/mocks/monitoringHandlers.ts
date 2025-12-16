import { http, HttpResponse, delay } from 'msw';
import {
  MOCK_HIERARCHY,
  getMockRegion,
  getMockVerfahren,
  getMockHost,
  getMockStats,
  regenerateMockHierarchy,
} from './monitoringMocks';
import type { Host, HostService } from '@/types/monitoring';

// Simulated network delay (ms)
const MOCK_DELAY = 200;

// ============================================================================
// Monitoring API Handlers
// ============================================================================

export const monitoringHandlers = [
  // GET /api/monitoring/hierarchy - Full hierarchy
  http.get('/api/monitoring/hierarchy', async () => {
    await delay(MOCK_DELAY);
    return HttpResponse.json(MOCK_HIERARCHY);
  }),

  // GET /api/monitoring/stats - Aggregated statistics
  http.get('/api/monitoring/stats', async () => {
    await delay(MOCK_DELAY);
    return HttpResponse.json(getMockStats());
  }),

  // GET /api/monitoring/regions/:regionId - Single region details
  http.get('/api/monitoring/regions/:regionId', async ({ params }) => {
    await delay(MOCK_DELAY);
    const region = getMockRegion(params.regionId as string);

    if (!region) {
      return HttpResponse.json(
        { error: 'Region not found' },
        { status: 404 }
      );
    }

    return HttpResponse.json(region);
  }),

  // GET /api/monitoring/verfahren/:verfahrenId - Single verfahren details
  http.get('/api/monitoring/verfahren/:verfahrenId', async ({ params }) => {
    await delay(MOCK_DELAY);
    const verfahren = getMockVerfahren(params.verfahrenId as string);

    if (!verfahren) {
      return HttpResponse.json(
        { error: 'Verfahren not found' },
        { status: 404 }
      );
    }

    return HttpResponse.json(verfahren);
  }),

  // GET /api/monitoring/hosts - List all hosts with optional filters
  http.get('/api/monitoring/hosts', async ({ request }) => {
    await delay(MOCK_DELAY);
    const url = new URL(request.url);
    const status = url.searchParams.get('status');
    const regionId = url.searchParams.get('region_id');
    const verfahrenId = url.searchParams.get('verfahren_id');

    let hosts: Host[] = [];

    // Collect all hosts
    for (const region of MOCK_HIERARCHY.regions) {
      if (regionId && region.id !== regionId) continue;

      for (const verfahren of region.verfahren) {
        if (verfahrenId && verfahren.id !== verfahrenId) continue;
        hosts.push(...verfahren.hosts);
      }
    }

    // Apply status filter
    if (status) {
      hosts = hosts.filter((h) => h.status === status);
    }

    return HttpResponse.json({
      items: hosts,
      total: hosts.length,
    });
  }),

  // GET /api/monitoring/hosts/:hostId - Single host details
  http.get('/api/monitoring/hosts/:hostId', async ({ params }) => {
    await delay(MOCK_DELAY);
    const host = getMockHost(params.hostId as string);

    if (!host) {
      return HttpResponse.json(
        { error: 'Host not found' },
        { status: 404 }
      );
    }

    return HttpResponse.json(host);
  }),

  // POST /api/monitoring/hosts/:hostId/refresh - Refresh/ping a host
  http.post('/api/monitoring/hosts/:hostId/refresh', async ({ params }) => {
    await delay(MOCK_DELAY + 500); // Longer delay for "ping"
    const host = getMockHost(params.hostId as string);

    if (!host) {
      return HttpResponse.json(
        { error: 'Host not found' },
        { status: 404 }
      );
    }

    // Simulate updated host with fresh lastCheck
    const updatedHost: Host = {
      ...host,
      lastCheck: new Date(),
      // Randomly improve status sometimes
      status: Math.random() > 0.8 && host.status === 'warning' ? 'online' : host.status,
    };

    return HttpResponse.json(updatedHost);
  }),

  // POST /api/monitoring/hosts/:hostId/services/:serviceName/check - Check specific service
  http.post(
    '/api/monitoring/hosts/:hostId/services/:serviceName/check',
    async ({ params }) => {
      await delay(MOCK_DELAY + 300);
      const host = getMockHost(params.hostId as string);

      if (!host) {
        return HttpResponse.json(
          { error: 'Host not found' },
          { status: 404 }
        );
      }

      const service = host.services.find(
        (s) => s.name === params.serviceName
      );

      if (!service) {
        return HttpResponse.json(
          { error: 'Service not found' },
          { status: 404 }
        );
      }

      // Simulate service check result
      const updatedService: HostService = {
        ...service,
        // Randomly "fix" error services
        status:
          service.status === 'error' && Math.random() > 0.5
            ? 'running'
            : service.status,
      };

      return HttpResponse.json(updatedService);
    }
  ),

  // POST /api/monitoring/refresh - Refresh entire hierarchy (admin action)
  http.post('/api/monitoring/refresh', async () => {
    await delay(MOCK_DELAY * 3);
    const newHierarchy = regenerateMockHierarchy();
    return HttpResponse.json(newHierarchy);
  }),
];

// ============================================================================
// Browser MSW Setup (for development)
// ============================================================================

export async function setupMonitoringMocks() {
  if (typeof window === 'undefined') return;

  const { setupWorker } = await import('msw/browser');
  const worker = setupWorker(...monitoringHandlers);

  await worker.start({
    onUnhandledRequest: 'bypass', // Don't warn about other requests
  });

  console.log('[MSW] Monitoring mocks enabled');
  return worker;
}
