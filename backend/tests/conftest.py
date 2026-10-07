import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
import types

from app.main import app
from app.db.base import Base
from app.api.deps import get_db


class _FlattenedRoute:
    """Lightweight proxy for a concrete route under an included router.

    Exposes `path` (prefix + child path = the effective request path),
    `methods`, `name` and `endpoint` so route-inventory assertions can be
    written identically for flat (older FastAPI) and nested (newer
    FastAPI) registration.
    """

    __slots__ = ("path", "methods", "name", "endpoint")

    def __init__(self, child, prefix: str):
        self.path = prefix + getattr(child, "path", "")
        self.methods = getattr(child, "methods", None)
        self.name = getattr(child, "name", "")
        self.endpoint = getattr(child, "endpoint", None)


def iter_flattened_routes(routes=None):
    """Yield every concrete route, descending into nested _IncludedRouter
    wrappers.

    FastAPI >= 0.135 stopped flattening included routers into app.routes:
    each include_router(...) now appends a single lazy _IncludedRouter
    object and the real APIRoute objects live inside it, prefixed by the
    include_router(...) prefix. The older route-inventory tests inspect
    getattr(r, "path", "") on app.routes directly; this helper yields
    route-like proxies with the effective paths so those assertions work
    on both flat and nested registrations without changing what is
    asserted.
    """
    if routes is None:
        routes = app.routes
    for r in routes:
        if type(r).__name__ == "_IncludedRouter":
            ctx = getattr(r, "include_context", None)
            prefix = getattr(ctx, "prefix", "") if ctx is not None else ""
            for child in getattr(r, "original_router").routes:
                if type(child).__name__ == "_IncludedRouter":
                    yield from iter_flattened_routes([child])
                else:
                    yield _FlattenedRoute(child, prefix)
        else:
            yield r

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def db_engine():
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    del app.dependency_overrides[get_db]
