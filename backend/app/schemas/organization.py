from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.organization import OrganizationRole

# --- Team Schemas ---
class TeamBase(BaseModel):
    name: str
    description: Optional[str] = None

class TeamCreate(TeamBase):
    slug: str

class TeamUpdate(TeamBase):
    pass

class TeamResponse(TeamBase):
    id: UUID
    organization_id: UUID
    slug: str
    created_by: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class TeamMemberResponse(BaseModel):
    id: UUID
    team_id: UUID
    user_id: UUID
    joined_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# --- Organization Schemas ---
class OrganizationBase(BaseModel):
    name: str
    description: Optional[str] = None
    logo_url: Optional[str] = None

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(OrganizationBase):
    pass

class OrganizationResponse(OrganizationBase):
    id: UUID
    slug: str
    created_by: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class OrganizationMemberResponse(BaseModel):
    id: UUID
    organization_id: UUID
    user_id: UUID
    role: OrganizationRole
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)

class OrganizationMemberUpdate(BaseModel):
    role: OrganizationRole

# --- Invitation Schemas ---
class InvitationCreate(BaseModel):
    email: str
    role: OrganizationRole = OrganizationRole.MEMBER

class InvitationResponse(BaseModel):
    id: UUID
    organization_id: UUID
    email: str
    role: OrganizationRole
    invited_by: UUID
    expires_at: datetime
    accepted_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class InvitationAccept(BaseModel):
    token: str
