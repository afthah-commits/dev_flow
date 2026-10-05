import re

with open('backend/app/schemas/delivery.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_schema = '''class ReleaseReadiness(BaseModel):
    score: int
    task_completion_pct: float
    pipeline_health_pct: float
    blocked_tasks_penalty: int
    deployment_health_pct: float
    sprint_completion_pct: float
    explanations: List[str]'''

new_schema = '''class ReadinessCheck(BaseModel):
    name: str
    status: str
    message: str

class ReleaseReadiness(BaseModel):
    ready: bool
    score: int
    checks: List[ReadinessCheck]
    
class ReleaseApprovalCreate(BaseModel):
    reviewer_id: UUID
    comment: Optional[str] = None
    
class ReleaseApprovalResponse(BaseModel):
    id: UUID
    release_id: UUID
    requested_by_id: UUID
    reviewer_id: UUID
    status: str
    comment: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True'''

text = text.replace(old_schema, new_schema)

with open('backend/app/schemas/delivery.py', 'w', encoding='utf-8') as f:
    f.write(text)
