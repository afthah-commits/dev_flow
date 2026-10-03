from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import auth, projects, tasks, dashboard, github, ai, analytics, notifications, organizations, teams, invitations, labels, templates, sprints, milestones, backlog, roadmap, audit, time
from app.api.v1.delivery import (
    project_releases_router, releases_router, environments_router,
    project_deployments_router, deployments_router, pipelines_router,
    delivery_metrics_router
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
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

@app.get("/health")
def health_check():
    return {"status": "ok"}

