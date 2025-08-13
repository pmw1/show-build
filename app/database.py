"""
Database configuration and session management for Show-Build.
Server-centric architecture with PostgreSQL as the primary data store.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator

# Database URL configuration
# Docker: postgresql://user:password@postgres:5432/showbuild
# Dev: postgresql://user:password@localhost:5432/showbuild
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://showbuild:showbuild@postgres:5432/showbuild"
)

engine = create_engine(
    DATABASE_URL,
    # Connection pool settings for production
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=True if os.getenv("DEBUG") else False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()