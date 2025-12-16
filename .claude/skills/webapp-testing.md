---
name: webapp-testing
description: Generate web application tests for React frontend. Use when testing UI components and integration.
globs:
  - "client/src/**/*.tsx"
  - "client/src/**/*.ts"
  - "client/**/*.test.tsx"
  - "client/**/*.test.ts"
---

# Web Application Testing for eMMA

Generate tests for React frontend using Vitest and Testing Library.

## Test Framework
- **Vitest** - Test runner
- **@testing-library/react** - Component testing
- **@testing-library/user-event** - User interaction simulation
- **msw** - API mocking

## Test Structure
```typescript
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } }
});

const wrapper = ({ children }) => (
  <QueryClientProvider client={queryClient}>
    {children}
  </QueryClientProvider>
);
```

## Test Categories

### 1. Component Rendering
```typescript
describe('ServiceCard', () => {
  it('renders service name and status', () => {
    render(<ServiceCard service={mockService} />, { wrapper });

    expect(screen.getByText('My Service')).toBeInTheDocument();
    expect(screen.getByText('healthy')).toBeInTheDocument();
  });
});
```

### 2. User Interactions
```typescript
describe('LoginForm', () => {
  it('submits login form with credentials', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(<LoginForm onSubmit={onSubmit} />, { wrapper });

    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.type(screen.getByLabelText(/password/i), 'password123');
    await user.click(screen.getByRole('button', { name: /login/i }));

    expect(onSubmit).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password123'
    });
  });
});
```

### 3. API Integration (MSW)
```typescript
import { rest } from 'msw';
import { setupServer } from 'msw/node';

const server = setupServer(
  rest.get('/v1/services', (req, res, ctx) => {
    return res(ctx.json([
      { id: 1, name: 'Service 1', status: 'healthy' }
    ]));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('ServiceList', () => {
  it('fetches and displays services', async () => {
    render(<ServiceList />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Service 1')).toBeInTheDocument();
    });
  });
});
```

### 4. Error States
```typescript
it('displays error message on API failure', async () => {
  server.use(
    rest.get('/v1/services', (req, res, ctx) => {
      return res(ctx.status(500));
    })
  );

  render(<ServiceList />, { wrapper });

  await waitFor(() => {
    expect(screen.getByText(/error loading services/i)).toBeInTheDocument();
  });
});
```

### 5. Zustand Store Testing
```typescript
import { useServiceStore } from '@/stores/serviceStore';

describe('serviceStore', () => {
  it('adds service to store', () => {
    const { result } = renderHook(() => useServiceStore());

    act(() => {
      result.current.addService({ id: 1, name: 'Test' });
    });

    expect(result.current.services).toHaveLength(1);
  });
});
```

## Running Tests
```bash
cd client
npm test              # Watch mode
npm run test:ci       # CI mode with coverage
npm run test:ui       # Visual UI
```

## Best Practices
1. Test behavior, not implementation
2. Use `getByRole` over `getByTestId`
3. Mock at network level with MSW
4. Test error and loading states
5. Use `userEvent` over `fireEvent`
