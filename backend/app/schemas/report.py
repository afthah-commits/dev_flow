from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.models.report import ReportType

class ReportBase(BaseModel):
    name: str
    description: Optional[str] = None
    report_type: ReportType
    configuration: Dict[str, Any] = {}

class ReportCreate(ReportBase):
    pass

class ReportUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None

class ReportResponse(ReportBase):
    id: str
    organization_id: str
    created_by_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class DashboardWidgetBase(BaseModel):
    widget_type: str
    title: str
    configuration: Dict[str, Any] = {}
    position_x: int = 0
    position_y: int = 0
    width: int = 1
    height: int = 1

class DashboardWidgetCreate(DashboardWidgetBase):
    pass

class DashboardWidgetUpdate(BaseModel):
    title: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None

class DashboardWidgetResponse(DashboardWidgetBase):
    id: str
    dashboard_id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DashboardBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_default: bool = False

class DashboardCreate(DashboardBase):
    pass

class DashboardUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None

class DashboardResponse(DashboardBase):
    id: str
    organization_id: str
    created_by_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    widgets: List[DashboardWidgetResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

class ReportFilter(BaseModel):
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    team_id: Optional[str] = None
    project_id: Optional[str] = None
    sprint_id: Optional[str] = None
    assignee_id: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None

