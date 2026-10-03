from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class AIMessageBase(BaseModel):
    role: str
    content: str

class AIMessageCreate(AIMessageBase):
    pass

class AIMessageResponse(AIMessageBase):
    id: UUID
    created_at: datetime
    class Config:
        from_attributes = True

class AIConversationBase(BaseModel):
    title: str
    project_id: Optional[UUID] = None

class AIConversationCreate(AIConversationBase):
    pass

class AIConversationResponse(AIConversationBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    messages: Optional[List[AIMessageResponse]] = None
    
    class Config:
        from_attributes = True

class AIChatRequest(BaseModel):
    message: str

class AIProjectSummaryRequest(BaseModel):
    pass

class AINextTaskRequest(BaseModel):
    pass

class AITaskDescriptionRequest(BaseModel):
    instruction: str

class AITaskBreakdownRequest(BaseModel):
    task_id: UUID

class AIReadmeRequest(BaseModel):
    pass

class TaskSuggestion(BaseModel):
    title: str
    description: str
    priority: str
    labels: List[str]

class TaskBreakdown(BaseModel):
    subtasks: List[TaskSuggestion]

class AIActionResponse(BaseModel):
    result: str
    structured_data: Optional[dict] = None
