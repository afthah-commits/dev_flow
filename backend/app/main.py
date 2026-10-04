from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import auth, projects, tasks, dashboard, github, ai, analytics, notifications, organizations, teams, invitations, labels, templates, sprints, milestones, backlog, roadmap, audit, time, jobs, realtime
from app.api.v1.delivery import (
    project_releases_router, releases_router, environments_router,
    project_deployments_router, deployments_router, pipelines_router,
    delivery_metrics_router
)
from app.api.v1 import collaboration, search, ws, knowledge

from app.api.v1 import environments, deployments, deployment_incidents, infrastructure

from app.api.v1 import reports, dashboards, governance, privacy
from app.api.v1 import automations, integrations, webhooks, api_keys
from app.api.public_v1 import public


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

from app.core.exceptions import add_exception_handlers
from app.core.middleware import CorrelationIdMiddleware

add_exception_handlers(app)
app.add_middleware(CorrelationIdMiddleware)


# Set all CORS enabled origins
allowed_origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",") if origin.strip()] if hasattr(settings, 'ALLOWED_ORIGINS') else [settings.FRONTEND_URL]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(organizations.router, prefix=f"{settings.API_V1_STR}/organizations", tags=["organizations"])
app.include_router(teams.router, prefix=f"{settings.API_V1_STR}", tags=["teams"])
app.include_router(invitations.router, prefix=f"{settings.API_V1_STR}/invitations", tags=["invitations"])
app.include_router(labels.router, prefix=f"{settings.API_V1_STR}/labels", tags=["labels"])
app.include_router(templates.router, prefix=f"{settings.API_V1_STR}/templates", tags=["templates"])
app.include_router(projects.router, prefix=f"{settings.API_V1_STR}/projects", tags=["projects"])
app.include_router(tasks.router, prefix=f"{settings.API_V1_STR}/projects/{{project_id}}/tasks", tags=["tasks"])
app.include_router(sprints.router, prefix=f"{settings.API_V1_STR}/projects/{{project_id}}/sprints", tags=["sprints"])
app.include_router(milestones.router, prefix=f"{settings.API_V1_STR}/projects/{{project_id}}/milestones", tags=["milestones"])
app.include_router(backlog.router, prefix=f"{settings.API_V1_STR}/projects/{{project_id}}/backlog", tags=["backlog"])
app.include_router(roadmap.router, prefix=f"{settings.API_V1_STR}/projects/{{project_id}}/roadmap", tags=["roadmap"])
app.include_router(dashboard.router, prefix=f"{settings.API_V1_STR}/dashboard", tags=["dashboard"])
app.include_router(github.router, prefix=f"{settings.API_V1_STR}/github", tags=["github"])
app.include_router(ai.router, prefix=f"{settings.API_V1_STR}/ai", tags=["ai"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_STR}/analytics", tags=["analytics"])
app.include_router(notifications.router, prefix=f"{settings.API_V1_STR}/notifications", tags=["notifications"])
app.include_router(audit.router, prefix=f"{settings.API_V1_STR}/audit", tags=["audit"])
app.include_router(time.router, prefix=f"{settings.API_V1_STR}/time", tags=["Time Tracking"])

# Phase 13: Delivery
app.include_router(project_releases_router, prefix=f"{settings.API_V1_STR}/projects/{{project_id}}/releases", tags=["releases"])
app.include_router(releases_router, prefix=f"{settings.API_V1_STR}/releases", tags=["releases"])
app.include_router(environments_router, prefix=f"{settings.API_V1_STR}/projects/{{project_id}}/environments", tags=["environments"])
app.include_router(project_deployments_router, prefix=f"{settings.API_V1_STR}/projects/{{project_id}}/deployments", tags=["deployments"])
app.include_router(deployments_router, prefix=f"{settings.API_V1_STR}/deployments", tags=["deployments"])
app.include_router(pipelines_router, prefix=f"{settings.API_V1_STR}/projects/{{project_id}}/pipelines", tags=["pipelines"])
app.include_router(delivery_metrics_router, prefix=f"{settings.API_V1_STR}/analytics", tags=["delivery-analytics"])

# Phase 14: Collaboration
app.include_router(collaboration.comments_router, prefix=f"{settings.API_V1_STR}/comments", tags=["comments"])
app.include_router(collaboration.discussions_router, prefix=f"{settings.API_V1_STR}", tags=["discussions"])
app.include_router(collaboration.attachments_router, prefix=f"{settings.API_V1_STR}/attachments", tags=["attachments"])
app.include_router(knowledge.router, prefix=f"{settings.API_V1_STR}/knowledge", tags=["knowledge"])
app.include_router(search.router, prefix=f"{settings.API_V1_STR}/search", tags=["search"])
app.include_router(ws.router, prefix=f"{settings.API_V1_STR}/ws", tags=["websocket"])

app.include_router(governance.router, prefix=f"{settings.API_V1_STR}/governance", tags=["governance"])
app.include_router(privacy.router, prefix=f"{settings.API_V1_STR}/privacy", tags=["privacy"])
app.include_router(reports.router, prefix=f"{settings.API_V1_STR}/reports", tags=["reports"])
app.include_router(dashboards.router, prefix=f"{settings.API_V1_STR}/dashboards", tags=["dashboards"])
app.include_router(automations.router, prefix=f"{settings.API_V1_STR}/automations", tags=["automations"])
app.include_router(integrations.router, prefix=f"{settings.API_V1_STR}/integrations", tags=["integrations"])
app.include_router(webhooks.router, prefix=f"{settings.API_V1_STR}/webhooks", tags=["webhooks"])
app.include_router(api_keys.router, prefix=f"{settings.API_V1_STR}/api_keys", tags=["api_keys"])
app.include_router(public.router, prefix=f"/api/public/v1", tags=["public"])
app.include_router(jobs.router, prefix=f"{settings.API_V1_STR}/jobs", tags=["jobs"])
app.include_router(realtime.router, prefix=f"{settings.API_V1_STR}/realtime", tags=["realtime"])

# Phase 21: DevOps, Deployment & Infrastructure Intelligence
app.include_router(environments.router, prefix=f"{settings.API_V1_STR}/environments", tags=["environments-infra"])
app.include_router(deployments.router, prefix=f"{settings.API_V1_STR}/deployments", tags=["deployments-infra"])
app.include_router(deployment_incidents.router, prefix=f"{settings.API_V1_STR}/deployment_incidents", tags=["deployment-incidents"])
app.include_router(infrastructure.router, prefix=f"{settings.API_V1_STR}/infrastructure", tags=["infrastructure"])



import time
from sqlalchemy import text
from app.api import deps
from fastapi import Depends
from sqlalchemy.orm import Session

start_time = time.time()

@app.get("/health/live", tags=["health"])
def health_live():
    return {"status": "ok", "uptime_seconds": time.time() - start_time}

@app.get("/health/ready", tags=["health"])
def health_ready(db: Session = Depends(deps.get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "ok", "uptime_seconds": time.time() - start_time}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Database not ready")

@app.get("/health", tags=["health"])
def health_check(db: Session = Depends(deps.get_db)):
    return health_ready(db)


from app.jobs.scheduler import scheduler

@app.on_event('startup')
def startup_event():
    if settings.JOB_SCHEDULER_ENABLED:
        scheduler.start()

@app.on_event('shutdown')
def shutdown_event():
    scheduler.stop()

