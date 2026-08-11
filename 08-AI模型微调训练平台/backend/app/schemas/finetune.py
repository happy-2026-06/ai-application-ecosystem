"""Pydantic schemas for fine-tuning."""
from datetime import datetime
from pydantic import BaseModel, Field


class FineTuneCreate(BaseModel):
    name: str = Field(..., max_length=200)
    base_model: str = Field(default="deepseek-chat")
    method: str = Field(default="qlora", pattern="^(qlora|lora|full)$")
    dataset_id: str | None = None
    learning_rate: float = Field(default=2e-4)
    epochs: int = Field(default=3, ge=1, le=20)
    batch_size: int = Field(default=4, ge=1, le=64)


class FineTuneResponse(BaseModel):
    id: str; user_id: str; name: str; base_model: str; method: str
    status: str; hyperparams: dict | None = None
    loss_history: list | None = None; eval_metrics: dict | None = None
    duration_seconds: int | None = None
    created_at: datetime; updated_at: datetime
    model_config = {"from_attributes": True}


class ModelVersionResponse(BaseModel):
    id: str; task_id: str; version_number: int; model_name: str
    file_path: str | None = None; size_mb: float | None = None
    is_deployed: bool; api_endpoint: str | None = None; created_at: datetime
    model_config = {"from_attributes": True}


class ABTestCreate(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=5000)


class ABTestResponse(BaseModel):
    id: str; task_id: str; prompt: str
    base_response: str | None = None; finetuned_response: str | None = None
    winner: str | None = None; created_at: datetime
    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    total_tasks: int; running_tasks: int; completed_tasks: int
    total_models: int; deployed_models: int; recent_tasks: list[FineTuneResponse]
