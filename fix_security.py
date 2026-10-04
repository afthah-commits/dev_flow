with open('backend/app/api/v1/security.py', 'r') as f:
    c = f.read()

history = '''
from app.models.security import LoginEvent
class LoginEventResponse(BaseModel):
    id: UUID
    timestamp: datetime
    success: bool
    ip_address: Optional[str]
    user_agent: Optional[str]
    failure_reason: Optional[str]
    device_info: Optional[str]

    class Config:
        from_attributes = True

@router.get("/login-history", response_model=List[LoginEventResponse])
def get_login_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 20
):
    events = db.query(LoginEvent).filter(LoginEvent.user_id == current_user.id).order_by(LoginEvent.timestamp.desc()).offset(skip).limit(limit).all()
    return events
'''
c += history

with open('backend/app/api/v1/security.py', 'w') as f:
    f.write(c)
