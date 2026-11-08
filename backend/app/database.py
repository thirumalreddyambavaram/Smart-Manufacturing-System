
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


# Create the MySQL connection URL safely
DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username=settings.DB_USER,
    password=settings.DB_PASSWORD,
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    database=settings.DB_NAME,
)

# Create database engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
)

# Create reusable database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# Base class for all database models
class Base(DeclarativeBase):
    pass


# Database session dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
