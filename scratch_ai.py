import re

with open('backend/app/api/v1/ai.py', 'r') as f:
    content = f.read()

ai_endpoint = """
class ClientSummaryRequest(BaseModel):
    client_id: str

@router.post("/client/summary")
async def generate_client_summary(
    req: ClientSummaryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    from app.services import client_service
    client = client_service.verify_client_access(db, UUID(req.client_id), current_user.id)
    
    # We use MockAI Provider here.
    return {"summary": "Based on the client-visible data, your project is on track. 2 requests are OPEN, and 5 tasks were completed."}
"""

content = content + ai_endpoint

with open('backend/app/api/v1/ai.py', 'w') as f:
    f.write(content)
