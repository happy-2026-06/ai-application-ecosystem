"""Pydantic schemas for data pipeline."""
from datetime import datetime
from pydantic import BaseModel, Field


class DataSetCreate(BaseModel):
    """Create a new dataset."""
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    source: str = Field(default="upload", pattern="^(upload|api|crawl|manual)$")


class DataSetResponse(BaseModel):
    """Dataset in list/detail views."""
    id: str
    user_id: str
    name: str
    description: str | None = None
    source: str
    item_count: int
    status: str
    tags: list | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DataVersionResponse(BaseModel):
    """Version snapshot."""
    id: str
    dataset_id: str
    version_number: int
    item_count: int
    change_log: str | None = None
    quality_score: float | None = None
    metadata: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AnnotationItem(BaseModel):
    """Single item for batch annotation."""
    text: str = Field(..., min_length=1, max_length=5000)
    index: int = Field(default=0)


class AnnotationRequest(BaseModel):
    """Batch annotation request."""
    items: list[AnnotationItem] = Field(..., min_items=1, max_items=50)


class AnnotationResponse(BaseModel):
    """AI annotation result."""
    id: str
    dataset_id: str
    data_item: str
    label: str | None = None
    category: str | None = None
    sentiment: str | None = None
    confidence: float | None = None
    is_verified: bool
    annotated_by: str
    created_at: datetime

    model_config = {"from_attributes": True}


class QualityReport(BaseModel):
    """Data quality report."""
    dataset_id: str
    dataset_name: str
    total_items: int
    annotated_items: int
    verified_items: int
    label_distribution: dict
    category_distribution: dict
    avg_confidence: float
    quality_score: float
    completeness: float  # % of items annotated


class DashboardStats(BaseModel):
    """Overview dashboard statistics."""
    total_datasets: int
    total_items: int
    total_annotations: int
    ai_annotated: int
    human_verified: int
    avg_quality_score: float
    recent_datasets: list[DataSetResponse]


class CleanRequest(BaseModel):
    """Data cleaning configuration."""
    remove_duplicates: bool = True
    remove_empty: bool = True
    normalize_text: bool = True
    custom_rules: list[str] | None = None
