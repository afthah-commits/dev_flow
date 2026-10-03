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
