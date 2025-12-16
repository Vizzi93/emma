---
name: emma-backend
description: eMMA backend development with FastAPI, SQLAlchemy and PostgreSQL. Use when working on server code.
globs:
  - "server/**/*.py"
  - "server/alembic/**/*"
---

# eMMA Backend Development

FastAPI backend with async SQLAlchemy and PostgreSQL.

## Project Structure
```
server/
├── app/
│   ├── api/           # API Routes (v1)
│   ├── core/          # Config, Auth, Middleware
│   ├── models/        # SQLAlchemy Models
│   ├── schemas/       # Pydantic Schemas
│   └── services/      # Business Logic
├── alembic/           # DB Migrations
└── tests/
```

## API Route Pattern
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.service import ServiceCreate, ServiceResponse
from app.services import service_crud

router = APIRouter(prefix="/services", tags=["services"])

@router.get("/", response_model=list[ServiceResponse])
async def get_services(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """Get all services for current user."""
    return await service_crud.get_multi(db, skip=skip, limit=limit)

@router.post("/", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    service_in: ServiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new service."""
    return await service_crud.create(db, obj_in=service_in, user_id=current_user.id)
```

## SQLAlchemy Model Pattern
```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class ServiceStatus(str, enum.Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    url = Column(String(500), nullable=False)
    type = Column(String(50), nullable=False)  # http, tcp, icmp
    status = Column(Enum(ServiceStatus), default=ServiceStatus.UNKNOWN)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="services")
    checks = relationship("ServiceCheck", back_populates="service")
```

## Pydantic Schema Pattern
```python
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Optional

class ServiceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., max_length=500)
    type: str = Field(..., pattern="^(http|tcp|icmp|dns)$")

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[str] = None
    type: Optional[str] = None

class ServiceResponse(ServiceBase):
    id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
```

## CRUD Service Pattern
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.service import Service
from app.schemas.service import ServiceCreate, ServiceUpdate

class ServiceCRUD:
    async def get(self, db: AsyncSession, id: int) -> Service | None:
        result = await db.execute(select(Service).where(Service.id == id))
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> list[Service]:
        result = await db.execute(select(Service).offset(skip).limit(limit))
        return result.scalars().all()

    async def create(
        self, db: AsyncSession, obj_in: ServiceCreate, user_id: int
    ) -> Service:
        db_obj = Service(**obj_in.model_dump(), user_id=user_id)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, db_obj: Service, obj_in: ServiceUpdate
    ) -> Service:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, id: int) -> None:
        obj = await self.get(db, id)
        if obj:
            await db.delete(obj)
            await db.commit()

service_crud = ServiceCRUD()
```

## Alembic Migration
```bash
# Create migration
alembic revision --autogenerate -m "add services table"

# Run migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Authentication Dependency
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import verify_token
from app.models.user import User

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await user_crud.get(db, payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def require_role(roles: list[str]):
    async def role_checker(user: User = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return role_checker
```

## Commands
```bash
# Dev server
uvicorn app.main:app --reload --port 8000

# Tests
pytest tests/ -v

# Linting
ruff check .

# Type checking
mypy app
```
