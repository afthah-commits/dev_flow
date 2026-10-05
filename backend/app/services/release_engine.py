from typing import Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.delivery import Release, ReleaseTask, ReleaseStatus, Environment, Deployment, DeploymentStatus
from app.models.task import Task, TaskStatus
from app.models.infrastructure import ServiceHealth
from app.models.audit import AuditEvent

class ReleaseEngine:
    @staticmethod
    def evaluate_readiness(db: Session, release: Release) -> Dict[str, Any]:
        """
        Evaluate if a release is ready to be approved and deployed.
        Returns a dict: { "ready": bool, "score": int, "checks": list }
        """
        checks = []
        score = 0
        total_weight = 40
        ready = True
        
        # 1. Check Tasks (Weight: 10)
        tasks = db.query(Task).join(ReleaseTask).filter(ReleaseTask.release_id == release.id).all()
        if not tasks:
            checks.append({"name": "Linked Tasks", "status": "WARNING", "message": "No tasks linked to this release."})
            score += 5 # Partial score for no tasks
        else:
            incomplete = [t for t in tasks if t.status != TaskStatus.DONE]
            if incomplete:
                checks.append({
                    "name": "Linked Tasks",
                    "status": "FAIL",
                    "message": f"{len(incomplete)}/{len(tasks)} tasks are incomplete."
                })
                ready = False
            else:
                checks.append({
                    "name": "Linked Tasks",
                    "status": "PASS",
                    "message": f"All {len(tasks)} tasks are DONE."
                })
                score += 10
                
        # 2. Check Release Notes (Weight: 10)
        if not release.description or len(release.description.strip()) < 10:
            checks.append({"name": "Release Notes", "status": "FAIL", "message": "Release description is empty or too short."})
            ready = False
        else:
            checks.append({"name": "Release Notes", "status": "PASS", "message": "Release notes are documented."})
            score += 10
            
        # 3. Target Environment (Weight: 10)
        if not release.target_environment:
            checks.append({"name": "Target Environment", "status": "FAIL", "message": "No target environment specified."})
            ready = False
        else:
            env = db.query(Environment).filter(
                Environment.project_id == release.project_id,
                Environment.name == release.target_environment
            ).first()
            if not env:
                checks.append({"name": "Target Environment", "status": "WARNING", "message": f"Target environment '{release.target_environment}' not found."})
                score += 5
            else:
                checks.append({"name": "Target Environment", "status": "PASS", "message": f"Target environment '{release.target_environment}' is valid."})
                score += 10
                
        # 4. Approvals Check (Weight: 10)
        # Note: A release doesn't need to be already approved to be 'READY', 
        # but the readiness engine might just verify if it CAN be approved.
        # We will just verify if the release is not CANCELLED/FAILED.
        if release.status in [ReleaseStatus.CANCELLED, ReleaseStatus.FAILED]:
            checks.append({"name": "Release State", "status": "FAIL", "message": f"Release is {release.status.value}."})
            ready = False
        else:
            checks.append({"name": "Release State", "status": "PASS", "message": "Release is active."})
            score += 10
            
        # 4. Workflows Check (Weight: 10)
        from app.models.workflow import WorkflowExecution
        executions = db.query(WorkflowExecution).filter(WorkflowExecution.entity_id == release.id).all()
        if executions:
            active = [e for e in executions if e.status == "ACTIVE"]
            if active:
                checks.append({"name": "Workflows", "status": "FAIL", "message": f"{len(active)} workflows are still pending."})
                ready = False
            else:
                checks.append({"name": "Workflows", "status": "PASS", "message": "All attached workflows completed."})
                score += 10
        else:
            checks.append({"name": "Workflows", "status": "PASS", "message": "No workflows attached."})
            score += 10
            
        final_score = int((score / 50) * 100)
        
        return {
            "ready": ready,
            "score": final_score,
            "checks": checks
        }

    @staticmethod
    def check_environment_health(db: Session, environment_id: str) -> str:
        """
        Check the deterministic health of an environment.
        Returns 'HEALTHY', 'DEGRADED', or 'UNHEALTHY'
        """
        services = db.query(ServiceHealth).filter(ServiceHealth.environment_id == environment_id).all()
        if not services:
            return "HEALTHY" # Default if no specific services tracked
            
        unhealthy = sum(1 for s in services if s.status == "DOWN")
        degraded = sum(1 for s in services if s.status == "DEGRADED")
        
        if unhealthy > 0:
            return "UNHEALTHY"
        elif degraded > 0:
            return "DEGRADED"
        return "HEALTHY"
