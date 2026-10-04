from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User
from app.schemas.token import TokenPayload
from uuid import UUID

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    try:
        user_id = UUID(token_data.sub)
    except ValueError:
        raise HTTPException(status_code=403, detail="Invalid token subject")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    from app.core.context import set_current_user_id
    set_current_user_id(user.id)
    return user


from app.models.organization import OrganizationMember, OrganizationRole
from fastapi import Header
from typing import Optional

def get_current_organization_id(
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-Id")
) -> Optional[UUID]:
    if not x_organization_id:
        return None
    try:
        return UUID(x_organization_id)
    except ValueError:
        return None

def require_organization_member(
    db: Session, user_id: UUID, organization_id: UUID, allowed_roles: list[OrganizationRole] = None
) -> OrganizationMember:
    member = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == organization_id,
        OrganizationMember.user_id == user_id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this organization"
        )
        
    if allowed_roles and member.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have the required role in this organization"
        )
        
    from app.core.context import set_current_org_id
    set_current_org_id(organization_id)
        
    return member

from fastapi.security import APIKeyHeader
from app.models.api_key import APIKey
import hashlib
from datetime import datetime, timezone
import json

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

def get_api_key_auth(
    db: Session = Depends(get_db),
    api_key: str = Depends(api_key_header)
) -> APIKey:
    if not api_key:
        raise HTTPException(status_code=401, detail="API Key required")
    
    if api_key.startswith("Bearer "):
        api_key = api_key[7:]
        
    hashed = hashlib.sha256(api_key.encode('utf-8')).hexdigest()
    
    db_key = db.query(APIKey).filter(APIKey.key_hash == hashed).first()
    if not db_key:
        raise HTTPException(status_code=401, detail="Invalid API Key")
        
    if db_key.revoked_at:
        raise HTTPException(status_code=401, detail="API Key revoked")
        
    if db_key.expires_at and db_key.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="API Key expired")
        
    db_key.last_used_at = datetime.now(timezone.utc)
    db.commit()
    
    return db_key
