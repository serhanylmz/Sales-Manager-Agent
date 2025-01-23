from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import Settings
from .models import Base

settings = Settings()

# Add pool_recycle and timeout
engine = create_engine(
    settings.database_url,
    pool_recycle=3600,  # Recycle connections every hour
    connect_args={"check_same_thread": False}  # For SQLite only
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def init_db():
    Base.metadata.create_all(bind=engine)
    engine.dispose()  # Close all connections after init

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # Ensure connection is released
        engine.dispose()  # Extra cleanup