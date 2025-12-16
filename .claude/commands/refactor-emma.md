---
description: Systematic refactoring for eMMA codebase following best practices
argument-hint: [target]
---

# Refactoring Command for eMMA

Systematic, safe refactoring following eMMA coding standards and best practices.

## Refactoring Target
Target: $ARGUMENTS

Available targets:
- `api-routes` - Refactor FastAPI route handlers
- `services` - Extract business logic to service layer
- `models` - Improve SQLAlchemy models
- `components` - Refactor React components
- `hooks` - Extract and optimize React hooks
- `stores` - Improve Zustand stores
- `utils` - Consolidate utility functions
- `tests` - Improve test organization

## Refactoring Principles

### 1. Safety First
- Create tests before refactoring if missing
- Make small, incremental changes
- Verify after each change
- Keep functionality identical

### 2. Follow eMMA Standards
Reference EMMA_PROJECT_CONTEXT.md for:
- Naming conventions
- Code organization
- Error handling patterns
- Type requirements

### 3. SOLID Principles
- **S**ingle Responsibility
- **O**pen/Closed
- **L**iskov Substitution
- **I**nterface Segregation
- **D**ependency Inversion

## Refactoring Patterns

### API Routes (`/refactor-emma api-routes`)

**Before:**
```python
@router.post("/services")
async def create_service(data: dict, db: Session = Depends(get_db)):
    service = Service(**data)
    db.add(service)
    db.commit()
    return service
```

**After:**
```python
@router.post("/services", response_model=ServiceResponse, status_code=201)
async def create_service(
    service_in: ServiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ServiceResponse:
    """Create a new service for monitoring."""
    return await service_crud.create(db, obj_in=service_in, user_id=current_user.id)
```

### Services (`/refactor-emma services`)

Extract business logic from routes to service classes:

```python
# services/service_monitor.py
class ServiceMonitor:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_health(self, service_id: int) -> HealthStatus:
        service = await self.get_service(service_id)
        checker = self._get_checker(service.type)
        return await checker.check(service.url)

    def _get_checker(self, service_type: str) -> BaseChecker:
        checkers = {
            "http": HTTPChecker(),
            "tcp": TCPChecker(),
            "icmp": ICMPChecker(),
        }
        return checkers.get(service_type, HTTPChecker())
```

### Models (`/refactor-emma models`)

Improve SQLAlchemy models:
- Add proper relationships
- Add indexes for query performance
- Implement soft deletes
- Add audit timestamps

```python
class Service(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "services"
    __table_args__ = (
        Index("ix_services_user_status", "user_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    # ...
```

### Components (`/refactor-emma components`)

**Before:**
```tsx
const ServiceList = () => {
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/services')
      .then(r => r.json())
      .then(setServices)
      .finally(() => setLoading(false));
  }, []);

  // 200+ lines of JSX...
}
```

**After:**
```tsx
const ServiceList = () => {
  const { data: services, isLoading } = useServices();

  if (isLoading) return <ServiceListSkeleton />;

  return (
    <div className="grid gap-4">
      {services?.map(service => (
        <ServiceCard key={service.id} service={service} />
      ))}
    </div>
  );
};
```

### Hooks (`/refactor-emma hooks`)

Extract reusable logic:

```typescript
// hooks/useServiceHealth.ts
export const useServiceHealth = (serviceId: number) => {
  const queryClient = useQueryClient();

  const { data: health } = useQuery({
    queryKey: ['service-health', serviceId],
    queryFn: () => api.get(`/v1/services/${serviceId}/health`),
    refetchInterval: 30000,
  });

  const triggerCheck = useMutation({
    mutationFn: () => api.post(`/v1/services/${serviceId}/check`),
    onSuccess: () => {
      queryClient.invalidateQueries(['service-health', serviceId]);
    },
  });

  return { health, triggerCheck, isHealthy: health?.status === 'healthy' };
};
```

### Stores (`/refactor-emma stores`)

Improve Zustand stores with slices:

```typescript
// stores/index.ts
interface AppState {
  auth: AuthSlice;
  ui: UISlice;
  services: ServicesSlice;
}

const useAppStore = create<AppState>()(
  devtools(
    persist(
      (...a) => ({
        ...createAuthSlice(...a),
        ...createUISlice(...a),
        ...createServicesSlice(...a),
      }),
      { name: 'emma-store' }
    )
  )
);
```

## Refactoring Checklist

Before starting:
- [ ] Tests exist or will be created
- [ ] Changes are understood
- [ ] Backup/commit current state

During refactoring:
- [ ] Small incremental changes
- [ ] Run tests after each change
- [ ] No functionality changes
- [ ] Follow eMMA standards

After refactoring:
- [ ] All tests pass
- [ ] Linting passes
- [ ] Types check
- [ ] Code review ready

## Commit Strategy

Use conventional commits:
```
refactor(<scope>): <description>

- What was changed
- Why it was changed
- What patterns were applied

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## Now Execute

Refactor target: **$ARGUMENTS**

1. Analyze current implementation
2. Ensure tests exist (create if needed)
3. Plan refactoring steps
4. Execute incrementally
5. Verify after each step
6. Commit with clear message
