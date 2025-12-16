"""Async script to reset admin password."""

import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.user import User
from app.core.auth import password_hasher


async def reset_admin_password():
    """Reset password for admin@emma.com to 'admin123'."""

    # Create engine directly with SQLite URL
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
        # Find admin user
        query = select(User).where(User.email == 'admin@emma.com')
        result = await session.execute(query)
        user = result.scalar_one_or_none()

        if user is None:
            print('User admin@emma.com nicht gefunden!')
            return

        # Hash new password and update
        new_password_hash = password_hasher.hash('admin123')
        user.password_hash = new_password_hash

        await session.commit()
        print('Passwort erfolgreich zurueckgesetzt!')
        print('Email: admin@emma.com')
        print('Passwort: admin123')

    await engine.dispose()


if __name__ == '__main__':
    asyncio.run(reset_admin_password())
