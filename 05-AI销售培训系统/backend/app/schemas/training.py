"""Pydantic schemas for training sessions and rounds."""
from datetime import datetime
from pydantic import BaseModel, Field


class TrainingSessionCreate(BaseModel):
    """Create a new training session."""
    customer_type: str = Field(..., pattern="^(picky|price|hesitant|expert)$")
    product_context: str | None = Field(None, max_length=2000)


class TrainingSessionResponse(BaseModel):
    """Training session in list/detail views."""
    id: str
    user_id: str
    customer_type: str
    product_context: str | None = None
    overall_score: float | None = None
    total_rounds: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TrainingRoundResponse(BaseModel):
    """A single round in a training session."""
    id: str
    training_session_id: str
    round_number: int
    user_response: str
    customer_response: str
    coach_hint: str | None = None
    scores: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TrainingRespondRequest(BaseModel):
    """Send a sales response in the training session."""
    response: str = Field(..., min_length=1, max_length=3000)


class TrainingReportResponse(BaseModel):
    """Complete training report."""
    session: TrainingSessionResponse
    rounds: list[TrainingRoundResponse]
    score_trend: list[dict]  # [{round, overall, fluency, persuasiveness, ...}]
    strengths: list[str]
    improvements: list[str]
    recommendation: str
