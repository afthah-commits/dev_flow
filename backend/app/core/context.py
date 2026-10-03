import contextvars
from typing import Optional
from uuid import UUID

_current_user_id: contextvars.ContextVar[Optional[UUID]] = contextvars.ContextVar(
    "current_user_id", default=None
)

_current_org_id: contextvars.ContextVar[Optional[UUID]] = contextvars.ContextVar(
    "current_org_id", default=None
)

def set_current_user_id(user_id: Optional[UUID]):
    return _current_user_id.set(user_id)

def get_current_user_id() -> Optional[UUID]:
    return _current_user_id.get()

def set_current_org_id(org_id: Optional[UUID]):
    return _current_org_id.set(org_id)

def get_current_org_id() -> Optional[UUID]:
    return _current_org_id.get()
