import re

with open('backend/app/services/automation_engine.py', 'r', encoding='utf-8') as f:
    text = f.read()

pattern = r'elif action_type == "CREATE_COMMENT":.*?action_exec\.output_data = \{"comment_id": str\(comment\.id\)\}'

new_comment_code = '''elif action_type == "CREATE_COMMENT":
                entity_id = action.get("entity_id") or event_payload.get("task_id") or event_payload.get("entity_id")
                author_id = action.get("author_id") or event_payload.get("actor_user_id") or event_payload.get("actor_id")
                if not author_id:
                    from app.models.automation import Automation
                    automation = db.query(Automation).filter(Automation.id == execution.automation_id).first()
                    author_id = automation.created_by if automation else None
                if entity_id and author_id:
                    comment = Comment(
                        organization_id=uuid.UUID(str(org_id)),
                        author_id=uuid.UUID(str(author_id)),
                        entity_type=action.get("entity_type", "TASK"),
                        entity_id=uuid.UUID(str(entity_id)),
                        content=action.get("content", "Automated comment")
                    )
                    db.add(comment)
                    db.flush()
                    action_exec.output_data = {"comment_id": str(comment.id)}'''

text = re.sub(pattern, new_comment_code, text, flags=re.DOTALL)

with open('backend/app/services/automation_engine.py', 'w', encoding='utf-8') as f:
    f.write(text)
