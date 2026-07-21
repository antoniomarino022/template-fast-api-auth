from typing import AsyncGenerator, Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from config.settings import settings


DATABASE_URL = settings.DATABASE_URL


engine = create_async_engine(
    DATABASE_URL, 
    echo=True,          # Mostra i log delle query SQL stampate nel terminale
    pool_pre_ping=True  # Riconnette automaticamente se la connessione MySQL scade (consigliato)
)

async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_session)]
