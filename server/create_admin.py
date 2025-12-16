"""Async script to create admin user."""

import asyncio
import sys
sys.path.insert(0, '.')

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.user import User, UserRole
from app.core.auth import password_hasher


async def create_admin():
    """Create admin user if not exists."""

    engine = create_async_engine(
        'sqlite+aiosqlite:///./emma.db',
        echo=False,
    )

    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        # Check if admin exists
        query = select(User).where(User.email == 'admin@example.com')
        result = await session.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            print('User existiert bereits!')
            await engine.dispose()
            return

        # Create admin user
        admin = User(
            id=uuid4(),
            email='admin@example.com',
            password_hash=password_hasher.hash('admin123'),
            full_name='Admin',
            role=UserRole.ADMIN.value,
            is_active=True,
            is_verified=True,
        )
        session.add(admin)
        await session.commit()
        print('Admin-User erstellt: admin@example.com / admin123')

    await engine.dispose()


if __name__ == '__main__':
    asyncio.run(create_admin())
