from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

# sqlite needs one extra option so tests can use it from more than one thread
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
# the engine is the main link to the database
# pool pre ping checks a connection still works before using it
engine = create_engine(settings.database_url, pool_pre_ping=True, connect_args=connect_args)
# a session factory that makes a new database session when we ask
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


# every table class builds on this base class
class Base(DeclarativeBase):
    pass


# give each request its own database session and always close it at the end
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
