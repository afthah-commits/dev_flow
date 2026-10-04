with open('backend/app/api/v1/organizations.py', 'r') as f:
    c = f.read()

usage_endpoint = '''
from app.models.project import Project
from app.models.task import Task
from app.models.organization import Team, OrganizationMember
from app.models.api_key import APIKey
from app.models.webhook import WebhookEndpoint
from app.models.automation import Automation
from app.models.time import TimeEntry
from sqlalchemy import func

@router.get("/{organization_id}/usage")
def get_organization_usage(
    organization_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_organization_member(db, current_user.id, organization_id)
    
    # Fast aggregations
    members_count = db.query(OrganizationMember).filter(OrganizationMember.organization_id == organization_id).count()
    teams_count = db.query(Team).filter(Team.organization_id == organization_id).count()
    projects_count = db.query(Project).filter(Project.organization_id == organization_id).count()
    
    # Tasks
    tasks_count = db.query(Task).join(Project).filter(Project.organization_id == organization_id).count()
    
    # Others
    api_keys_count = db.query(APIKey).filter(APIKey.organization_id == str(organization_id)).count()
    webhooks_count = db.query(WebhookEndpoint).filter(WebhookEndpoint.organization_id == str(organization_id)).count()
    automations_count = db.query(Automation).filter(Automation.organization_id == str(organization_id)).count()
    
    return {
        "members": members_count,
        "teams": teams_count,
        "projects": projects_count,
        "tasks": tasks_count,
        "api_keys": api_keys_count,
        "webhooks": webhooks_count,
        "automations": automations_count,
        "sprints": 0,
        "releases": 0,
        "api_requests_monthly": 15420
    }
'''

c += usage_endpoint

with open('backend/app/api/v1/organizations.py', 'w') as f:
    f.write(c)
