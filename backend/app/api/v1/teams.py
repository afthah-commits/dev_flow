from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List
from uuid import UUID
import re

from app.api import deps
from app.models.user import User
from app.models.organization import OrganizationRole, Team, TeamMember, OrganizationMember
from app.schemas.organization import TeamCreate, TeamUpdate, TeamResponse, TeamMemberResponse

router = APIRouter()

def generate_slug(name: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    return slug if slug else "team"

@router.post("/organizations/{organization_id}/teams", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(
    *,
    db: Session = Depends(deps.get_db),
    organization_id: UUID,
    team_in: TeamCreate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    deps.require_organization_member(db, current_user.id, organization_id, [OrganizationRole.OWNER, OrganizationRole.ADMIN])
    
    if db.query(Team).filter(Team.organization_id == organization_id, Team.slug == team_in.slug).first():
        raise HTTPException(status_code=400, detail="Team with this slug already exists")

    team = Team(
        **team_in.model_dump(),
        organization_id=organization_id,
        created_by=current_user.id
    )
    db.add(team)
    db.commit()
    db.refresh(team)
    return team

@router.get("/organizations/{organization_id}/teams", response_model=List[TeamResponse])
def list_teams(
    *,
    db: Session = Depends(deps.get_db),
    organization_id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    deps.require_organization_member(db, current_user.id, organization_id)
    teams = db.query(Team).filter(Team.organization_id == organization_id).all()
    return teams

@router.get("/teams/{team_id}", response_model=TeamResponse)
def get_team(
    *,
    db: Session = Depends(deps.get_db),
    team_id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    deps.require_organization_member(db, current_user.id, team.organization_id)
    return team

@router.patch("/teams/{team_id}", response_model=TeamResponse)
def update_team(
    *,
    db: Session = Depends(deps.get_db),
    team_id: UUID,
    team_in: TeamUpdate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    deps.require_organization_member(db, current_user.id, team.organization_id, [OrganizationRole.OWNER, OrganizationRole.ADMIN])
    
    update_data = team_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(team, field, value)
    db.commit()
    db.refresh(team)
    return team

@router.delete("/teams/{team_id}")
def delete_team(
    *,
    db: Session = Depends(deps.get_db),
    team_id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    deps.require_organization_member(db, current_user.id, team.organization_id, [OrganizationRole.OWNER, OrganizationRole.ADMIN])
    
    db.delete(team)
    db.commit()
    return {"message": "Team deleted"}

@router.get("/teams/{team_id}/members", response_model=List[TeamMemberResponse])
def get_team_members(
    *,
    db: Session = Depends(deps.get_db),
    team_id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    deps.require_organization_member(db, current_user.id, team.organization_id)
    
    return db.query(TeamMember).filter(TeamMember.team_id == team_id).all()

@router.post("/teams/{team_id}/members", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
def add_team_member(
    *,
    db: Session = Depends(deps.get_db),
    team_id: UUID,
    user_id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    deps.require_organization_member(db, current_user.id, team.organization_id, [OrganizationRole.OWNER, OrganizationRole.ADMIN])
    
    # ensure user is in org
    org_member = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == team.organization_id,
        OrganizationMember.user_id == user_id
    ).first()
    if not org_member:
        raise HTTPException(status_code=400, detail="User is not in the organization")
        
    if db.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id).first():
        raise HTTPException(status_code=400, detail="User already in team")
        
    tm = TeamMember(team_id=team_id, user_id=user_id)
    db.add(tm)
    db.commit()
    db.refresh(tm)
    return tm

@router.delete("/teams/{team_id}/members/{user_id}")
def remove_team_member(
    *,
    db: Session = Depends(deps.get_db),
    team_id: UUID,
    user_id: UUID,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if current_user.id != user_id:
        deps.require_organization_member(db, current_user.id, team.organization_id, [OrganizationRole.OWNER, OrganizationRole.ADMIN])
    
    tm = db.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id).first()
    if not tm:
        raise HTTPException(status_code=404, detail="Team member not found")
        
    db.delete(tm)
    db.commit()
    return {"message": "Team member removed"}
