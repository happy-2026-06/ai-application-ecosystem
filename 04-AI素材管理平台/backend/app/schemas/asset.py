"""Asset-related Pydantic schemas for 图库资产管家."""
from pydantic import BaseModel, Field
from datetime import datetime


class AssetUpdateRequest(BaseModel):
    """Request body for updating an asset's editable fields."""
    original_name: str | None = Field(None, min_length=1, max_length=255)
    tags: list[str] | None = Field(None, description="Manual tags")
    ai_description: str | None = Field(None, description="AI-generated description override")
    status: str | None = Field(None, pattern="^(processing|ready|archived)$")


class AssetResponse(BaseModel):
    """Full asset detail response."""
    id: str
    filename: str
    original_name: str
    file_type: str
    file_size: int
    tags: list[str] | None = None
    ai_tags: list[str] | None = None
    ai_description: str | None = None
    thumbnail_url: str | None = None
    width: int | None = None
    height: int | None = None
    duration_seconds: int | None = None
    status: str
    version: int
    created_at: str
    updated_at: str | None = None


class AssetListResponse(BaseModel):
    """Paginated asset list response."""
    items: list[AssetResponse]
    total: int
    page: int
    page_size: int


class AssetStatsResponse(BaseModel):
    """Quick stats for sidebar/dashboard."""
    total: int = 0
    tagged: int = 0
    total_size_bytes: int = 0
    by_type: dict[str, int] = Field(default_factory=dict)
    by_status: dict[str, int] = Field(default_factory=dict)


class PopularTagsResponse(BaseModel):
    """Popular tags from the asset collection."""
    tags: list[str]
