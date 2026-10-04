from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

kwargs = {}
if settings.DATABASE_URL.startswith("sqlite"):
    kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, **kwargs)

if settings.DATABASE_URL.startswith("sqlite"):
    from sqlalchemy import event
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

from app.db.audit_listener import setup_audit_listeners
setup_audit_listeners(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
