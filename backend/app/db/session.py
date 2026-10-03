from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

kwargs = {}
if settings.DATABASE_URL.startswith("sqlite"):
    kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, **kwargs)

from app.db.audit_listener import setup_audit_listeners
setup_audit_listeners(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
