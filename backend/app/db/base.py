from app.db.base_class import Base
from app.models.user import User
from app.models.project import Project
from app.models.task import Task
from app.models.github import GitHubConnection, ProjectGitHubRepository
from app.models.ai_conversation import AIConversation, AIMessage
from app.models.notification import Notification, NotificationPreference
from app.models.organization import Organization, OrganizationMember, OrganizationRole, Team, TeamMember, OrganizationInvitation
from app.models.sprint import Sprint, SprintSnapshot
from app.models.milestone import Milestone
from app.models.audit import AuditEvent
from app.models.time import TimeEntry, ActiveTimer
from app.models.delivery import Release, ReleaseTask, ReleasePullRequest, Environment, Deployment, PipelineRun
from app.models.collaboration import Comment, CommentReaction, Discussion, Attachment
from app.models.automation import Automation, AutomationExecution, AutomationActionExecution
from app.models.integration import Integration, IntegrationCredential, IntegrationLog
from app.models.webhook import WebhookEndpoint, WebhookDelivery
from app.models.api_key import APIKey
from app.models.security import Role, RolePermission, UserSession, LoginEvent
from app.models.job import Job, JobExecution
from app.models.report import Report
from app.models.dashboard import Dashboard, DashboardWidget
