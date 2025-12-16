---
name: error-handling
description: Implement proper error handling patterns. Use when handling exceptions and errors.
globs:
  - "**/*.py"
  - "**/*.ts"
  - "**/*.tsx"
---

# Error Handling Patterns for eMMA

Implement robust error handling across backend and frontend.

## Backend (FastAPI/Python)

### Custom Exceptions
```python
from fastapi import HTTPException, status

class AppException(Exception):
    """Base application exception."""
    def __init__(self, message: str, code: str = "APP_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)

class NotFoundError(AppException):
    def __init__(self, resource: str, id: int | str):
        super().__init__(f"{resource} with id {id} not found", "NOT_FOUND")

class AuthenticationError(AppException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_ERROR")

class AuthorizationError(AppException):
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, "FORBIDDEN")
```

### Exception Handler
```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    status_map = {
        "NOT_FOUND": 404,
        "AUTH_ERROR": 401,
        "FORBIDDEN": 403,
        "VALIDATION": 422,
    }
    return JSONResponse(
        status_code=status_map.get(exc.code, 500),
        content={"error": exc.code, "message": exc.message}
    )
```

### Service Layer Error Handling
```python
import logging
from typing import TypeVar, Generic

logger = logging.getLogger(__name__)
T = TypeVar("T")

class Result(Generic[T]):
    """Result type for operations that can fail."""
    def __init__(self, value: T | None = None, error: str | None = None):
        self.value = value
        self.error = error
        self.success = error is None

async def get_service(service_id: int) -> Service:
    try:
        service = await db.get(Service, service_id)
        if not service:
            raise NotFoundError("Service", service_id)
        return service
    except Exception as e:
        logger.error(f"Failed to get service {service_id}: {e}", exc_info=True)
        raise
```

### API Route Error Handling
```python
@router.get("/services/{service_id}")
async def get_service(service_id: int, db: AsyncSession = Depends(get_db)):
    service = await service_crud.get(db, service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service {service_id} not found"
        )
    return service
```

## Frontend (React/TypeScript)

### API Error Types
```typescript
interface ApiError {
  error: string;
  message: string;
  statusCode: number;
}

class ApiException extends Error {
  constructor(
    public statusCode: number,
    public code: string,
    message: string
  ) {
    super(message);
    this.name = 'ApiException';
  }
}
```

### React Query Error Handling
```typescript
import { useQuery } from '@tanstack/react-query';
import toast from 'react-hot-toast';

const useServices = () => {
  return useQuery({
    queryKey: ['services'],
    queryFn: fetchServices,
    onError: (error: ApiException) => {
      toast.error(error.message);
    },
    retry: (failureCount, error) => {
      // Don't retry on 4xx errors
      if (error.statusCode >= 400 && error.statusCode < 500) {
        return false;
      }
      return failureCount < 3;
    }
  });
};
```

### Error Boundary
```typescript
import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || <ErrorFallback error={this.state.error} />;
    }
    return this.props.children;
  }
}
```

### Async Error Handling
```typescript
const handleSubmit = async (data: FormData) => {
  try {
    await createService(data);
    toast.success('Service created');
  } catch (error) {
    if (error instanceof ApiException) {
      if (error.statusCode === 422) {
        // Validation error - show field errors
        setFieldErrors(error.message);
      } else {
        toast.error(error.message);
      }
    } else {
      toast.error('An unexpected error occurred');
      console.error(error);
    }
  }
};
```

## Best Practices
1. Always log errors with context
2. Never expose internal errors to users
3. Use specific exception types
4. Implement retry logic for transient errors
5. Show user-friendly error messages
6. Track errors for monitoring
