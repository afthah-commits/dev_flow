with open('backend/app/api/v1/ai.py', 'r') as f:
    content = f.read()

ai_endpoint = '''
@router.post("/automations/generate")
async def generate_automation(
    request: dict,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    prompt = request.get("prompt")
    # Mock generation
    return {
        "trigger_type": "TASK_STATUS_CHANGED",
        "conditions": {
            "logical_operator": "ALL",
            "conditions": [
                {"field": "task.status", "operator": "EQUALS", "value": "OVERDUE"}
            ]
        },
        "actions": [
            {
                "type": "CREATE_NOTIFICATION",
                "message": "Task is overdue"
            }
        ]
    }
'''
if "def generate_automation" not in content:
    content += ai_endpoint
    with open('backend/app/api/v1/ai.py', 'w') as f:
        f.write(content)
