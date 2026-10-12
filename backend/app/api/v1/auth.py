from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserLogin
from app.schemas.token import Token
from datetime import datetime
from app.core.rate_limit import rate_limit

router = APIRouter()

# Brute-force protection. Generous thresholds keep local development and the
# automated test suite unblocked while bounding request volume per IP.
AUTH_RATE_LIMIT = (100, 60)  # requests per 60s window per IP+path

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(deps.get_db),
              _rl: None = Depends(rate_limit(*AUTH_RATE_LIMIT))):
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user_obj = User(
        name=user_in.name,
        email=user_in.email,
        password_hash=security.get_password_hash(user_in.password),
    )
    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)

    # Bootstrap default organization for newly registered user
    from app.models.organization import Organization, OrganizationMember, OrganizationRole
    from app.api.v1.organizations import generate_slug
    org_name = f"{user_in.name}'s Workspace" if user_in.name else "My Workspace"
    base_slug = generate_slug(org_name)
    slug = base_slug
    counter = 1
    while db.query(Organization).filter(Organization.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    org = Organization(
        name=org_name,
        slug=slug,
        created_by=user_obj.id,
    )
    db.add(org)
    db.commit()
    db.refresh(org)

    member = OrganizationMember(
        organization_id=org.id,
        user_id=user_obj.id,
        role=OrganizationRole.OWNER,
    )
    db.add(member)
    db.commit()

    return user_obj

@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(deps.get_db),
          _rl: None = Depends(rate_limit(*AUTH_RATE_LIMIT))):
    user = db.query(User).filter(User.email == user_in.email).first()
    
    from app.services.audit_service import record_event
    
    if not user or not security.verify_password(user_in.password, user.password_hash):
        if user:
            record_event(db, organization_id=None, event_type="AUTH_LOGIN_FAILED", entity_type="USER", actor_user_id=user.id, entity_id=user.id)
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
        )
    
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    record_event(db, organization_id=None, event_type="AUTH_LOGIN", entity_type="USER", actor_user_id=user.id, entity_id=user.id)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.get("/me", response_model=UserResponse)
def read_user_me(current_user: User = Depends(deps.get_current_user)):
    return current_user
