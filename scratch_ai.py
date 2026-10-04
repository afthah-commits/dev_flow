import re

with open('backend/app/api/v1/ai.py', 'r') as f:
    content = f.read()

ai_endpoint = """
class AIWorkflowGenerateRequest(BaseModel):
    prompt: str

@router.post("/workflows/generate")
async def generate_workflow(
    req: AIWorkflowGenerateRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    # Mock AI response
    return {
        "name": "Generated Workflow",
        "entity_type": "TASK",
        "states": [
            {"name": "To Do", "key": "TODO", "is_initial": True, "position": 0},
            {"name": "In Progress", "key": "IN_PROGRESS", "position": 1},
            {"name": "Done", "key": "DONE", "is_terminal": True, "position": 2}
        ],
        "transitions": [
            {"name": "Start", "from_state_key": "TODO", "to_state_key": "IN_PROGRESS", "requires_approval": False},
            {"name": "Finish", "from_state_key": "IN_PROGRESS", "to_state_key": "DONE", "requires_approval": True}
        ]
    }
"""

if "/workflows/generate" not in content:
    content = content + ai_endpoint

with open('backend/app/api/v1/ai.py', 'w') as f:
    f.write(content)
