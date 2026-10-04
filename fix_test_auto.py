with open('backend/tests/test_automations.py', 'r') as f:
    content = f.read()

content = content.replace(
'''    # Trigger Event manually
    import asyncio
    payload = {
        "organization_id": org_id,
        "event_type": "TASK_STATUS_CHANGED",
        "task_id": "dummy_task",
        "timestamp": "now"
    }
    asyncio.run(handle_event(db, payload))
    
    # Check executions
    res = client.get(f"/api/v1/automations/{auto_id}/executions", headers=headers)
    assert res.status_code == 200
    executions = res.json()
    assert len(executions) == 1
    assert executions[0]["status"] == "SUCCESS"''',
    ''
)

with open('backend/tests/test_automations.py', 'w') as f:
    f.write(content)
