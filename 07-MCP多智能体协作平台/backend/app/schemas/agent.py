"""Pydantic schemas for Agent/Task/Execution."""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class AgentCreate(BaseModel):
    """Register a new agent."""
    name: str = Field(..., max_length=100)
    role: str = Field(..., max_length=100)
    capability: str = Field(default="general")


class AgentResponse(BaseModel):
    """Agent detail."""
    id: str; name: str; role: str; capability: str; status: str
    system_prompt: str | None = None
    last_heartbeat: datetime | None = None
    created_at: datetime; updated_at: datetime
    model_config = {"from_attributes": True}


class TaskCreate(BaseModel):
    """Create a new task."""
    title: str = Field(..., max_length=200)
    description: str | None = None
    mode: str = Field(default="pipeline")
    agent_ids: list[str] = Field(default_factory=list)


class TaskResponse(BaseModel):
    id: str; user_id: str; title: str; description: str | None = None
    mode: str; status: str; result: str | None = None
    created_at: datetime; updated_at: datetime
    model_config = {"from_attributes": True}


class ExecutionResponse(BaseModel):
    id: str; task_id: str; agent_id: str; step_order: int
    input_data: str | None = None; output_data: str | None = None
    status: str; duration_ms: int | None = None; created_at: datetime
    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    total_agents: int; online_agents: int; total_tasks: int
    completed_tasks: int; running_tasks: int; recent_tasks: list[TaskResponse]
