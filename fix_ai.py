import codecs

with open('backend/app/api/v1/ai.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_endpoints = '''

@router.post("/projects/{project_id}/discussions/{discussion_id}/summary")
async def summarize_discussion(
    project_id: UUID,
    discussion_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id),
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    from app.models.collaboration import Discussion, Comment
    disc = db.query(Discussion).filter(Discussion.id == discussion_id, Discussion.project_id == project_id).first()
    if not disc:
        raise HTTPException(status_code=404, detail="Discussion not found")
    comments = db.query(Comment).filter(Comment.entity_id == discussion_id).all()
    
    prompt = f"Summarize discussion '{disc.title}': {disc.content}\\nComments: " + " ".join([c.content for c in comments])
    provider = get_ai_provider()
    messages = [{"role": "user", "content": prompt}]
    notes = await provider.chat(messages=messages, system_prompt=SYSTEM_PROMPT)
    return {"summary": notes}

@router.post("/projects/{project_id}/activity/summary")
async def summarize_activity(
    project_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id),
) -> Any:
    deps.require_organization_member(db, current_user.id, org_id)
    prompt = "Summarize recent activity in the project."
    provider = get_ai_provider()
    messages = [{"role": "user", "content": prompt}]
    notes = await provider.chat(messages=messages, system_prompt=SYSTEM_PROMPT)
    return {"summary": notes}
'''

content += new_endpoints

with open('backend/app/api/v1/ai.py', 'w', encoding='utf-8') as f:
    f.write(content)
