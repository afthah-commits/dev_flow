from .base import AIProvider
from typing import List, Dict, Any, Optional
import json

class MockAIProvider(AIProvider):
    async def chat(self, messages: List[Dict[str, str]], system_prompt: str, json_schema: Optional[Dict] = None) -> str:
        last_msg = messages[-1]["content"].lower()
        
        if json_schema:
            props = json_schema.get("properties", {})
            if "subtasks" in props:
                if "AIPlanningSuggestion" in json.dumps(json_schema):
                    # Phase 48 progressive (nested) breakdown contract:
                    # deterministic 2-level sample within max-3-level bounds.
                    return json.dumps({
                        "subtasks": [
                            {"title": "Backend payment integration", "description": "Auto generated", "priority": "HIGH",
                             "suggestion_id": "s1", "estimated_points": 5,
                             "children": [
                                 {"title": "Payment provider configuration", "description": "Auto generated", "priority": "MEDIUM",
                                  "suggestion_id": "s1a", "estimated_points": 2, "children": []},
                                 {"title": "Payment service", "description": "Auto generated 2", "priority": "MEDIUM",
                                  "suggestion_id": "s1b", "estimated_points": 3, "children": []},
                                 {"title": "Error handling", "description": "", "priority": "LOW",
                                  "suggestion_id": "s1c", "estimated_points": 1, "children": []},
                             ]},
                            {"title": "Frontend checkout", "description": "Auto generated", "priority": "MEDIUM",
                             "suggestion_id": "s2", "estimated_points": 3,
                             "children": [
                                 {"title": "Checkout UI", "description": "", "priority": "MEDIUM",
                                  "suggestion_id": "s2a", "estimated_points": 2, "children": []},
                                 {"title": "Payment state handling", "description": "", "priority": "LOW",
                                  "suggestion_id": "s2b", "estimated_points": 1, "children": []},
                             ]},
                            {"title": "Webhook handling", "description": "", "priority": "HIGH",
                             "suggestion_id": "s3", "estimated_points": 2, "children": []},
                            {"title": "Testing", "description": "", "priority": "MEDIUM",
                             "suggestion_id": "s4", "estimated_points": 2, "children": []},
                        ]
                    })
                return json.dumps({
                    "subtasks": [
                        {"title": "Subtask 1", "description": "Auto generated", "priority": "MEDIUM", "labels": ["ai"]},
                        {"title": "Subtask 2", "description": "Auto generated 2", "priority": "LOW", "labels": ["ai"]}
                    ]
                })
            elif "current_status" in props: # ProjectSummary
                return json.dumps({
                    "current_status": "Healthy",
                    "progress": "On track",
                    "health": "Good",
                    "major_completed_work": ["Setup", "DB"],
                    "overdue_work": [],
                    "blockers": [],
                    "sprint_status": "Active",
                    "github_activity": "High",
                    "deployment_status": "Stable",
                    "risks": [],
                    "recommended_next_actions": ["Review PRs"]
                })
            elif "severity" in props: # ProjectRisk
                return json.dumps({
                    "title": "Mock Risk",
                    "severity": "LOW",
                    "category": "Technology",
                    "explanation": "Just testing.",
                    "evidence": [],
                    "recommendation": "None."
                })
            elif "score" in props: # TaskPrioritySuggestion
                import uuid
                return json.dumps({
                    "task_id": str(uuid.uuid4()),
                    "task_key": "TASK-1",
                    "priority": "HIGH",
                    "score": 0.9,
                    "reason": "Crucial",
                    "blockers": [],
                    "recommendation": "Do it now"
                })
            elif "expected_sprint_outcome" in props: # SprintPlan
                return json.dumps({
                    "recommended_tasks": [],
                    "estimated_workload": "Low",
                    "risks": [],
                    "expected_sprint_outcome": "Done",
                    "excluded_tasks_with_reasons": {}
                })
            elif "recent_development_summary" in props: # GitHubSummary
                return json.dumps({
                    "recent_development_summary": "Active",
                    "pr_activity": "Normal",
                    "issue_trends": "Down",
                    "potential_risks": [],
                    "stale_prs": [],
                    "unresolved_issues": [],
                    "engineering_activity": "High"
                })
            elif "deployment_readiness" in props: # ReleaseAnalysis
                return json.dumps({
                    "release_summary": "Ready",
                    "completed_work": [],
                    "incomplete_tasks": [],
                    "pr_summary": "All merged",
                    "deployment_readiness": "Ready",
                    "blockers": [],
                    "risks": [],
                    "recommended_checks": []
                })
            elif "deployment_health" in props: # DeploymentAnalysis
                return json.dumps({
                    "deployment_health": "Healthy",
                    "recurring_failures": [],
                    "likely_risk_areas": [],
                    "recommended_checks": []
                })
            elif "completed_yesterday" in props: # DailyEngineeringBrief
                return json.dumps({
                    "completed_yesterday": [],
                    "active_today": [],
                    "overdue": [],
                    "blocked": [],
                    "github_changes": "None",
                    "pr_activity": "Low",
                    "deployment_changes": "None",
                    "important_risks": [],
                    "recommended_focus": "Code"
                })
            elif "title" in props:
                return json.dumps({
                    "title": "Generated Task", "description": "This is a mock description.", "priority": "HIGH", "labels": ["mock"]
                })
        
        if "summary" in last_msg:
            return "This is a mock summary of your project. It looks healthy!"
        if "next" in last_msg:
            return "You should probably work on the overdue tasks first."
        if "readme" in last_msg:
            return "# Mock README\n\nThis is a generated readme."
            
        return "I am a mock AI. I see you said: " + messages[-1]["content"]
