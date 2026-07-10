"""Watchlist models — MongoDB document schemas and Pydantic validation."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field


class RegexPattern(BaseModel):
    pattern: str
    label: str = ""
    case_sensitive: bool = False


class WatchlistCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    description: Optional[str] = Field(None, max_length=1024)
    keywords: List[str] = Field(default=[], max_length=1000)
    regex_patterns: List[RegexPattern] = Field(default=[], max_length=100)
    entities: List[str] = Field(default=[], max_length=100)
    severity_boost: int = Field(default=100, ge=0, le=1000)
    is_active: bool = True


class WatchlistUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=256)
    description: Optional[str] = Field(None, max_length=1024)
    keywords: Optional[List[str]] = Field(None, max_length=1000)
    regex_patterns: Optional[List[RegexPattern]] = Field(None, max_length=100)
    entities: Optional[List[str]] = Field(None, max_length=100)
    severity_boost: Optional[int] = Field(None, ge=0, le=1000)
    is_active: Optional[bool] = None


class WatchlistResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    keywords: List[str] = []
    regex_patterns: List[RegexPattern] = []
    entities: List[str] = []
    severity_boost: int = 100
    is_active: bool = True
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    match_count: int = 0


def new_watchlist_document(body: WatchlistCreate, user_id: str) -> dict:
    """Create a new watchlist document for MongoDB."""
    now = datetime.now(timezone.utc)
    return {
        "_id": str(uuid.uuid4()),
        "name": body.name,
        "description": body.description or "",
        "keywords": body.keywords,
        "regex_patterns": [p.dict() for p in body.regex_patterns],
        "entities": body.entities,
        "severity_boost": body.severity_boost,
        "is_active": body.is_active,
        "match_count": 0,
        "last_match_at": None,
        "created_by": user_id,
        "created_at": now,
        "updated_at": now,
    }
