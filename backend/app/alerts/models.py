"""Alert models — MongoDB document schemas and Pydantic validation."""

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field


class AlertCondition(BaseModel):
    """A single alert rule condition."""
    field: str
    operator: str  # "in", "contains_any", "gt", "lt", "eq", "ne"
    value: Any


class AlertNotification(BaseModel):
    """Notification configuration for an alert rule."""
    type: str = Field(..., pattern="^(email|webhook|dashboard_alert|sms)$")
    target: Optional[str] = None
    config: Optional[Dict] = None


class AlertRuleCreate(BaseModel):
    """Create alert rule payload."""
    name: str = Field(..., min_length=1, max_length=256)
    description: Optional[str] = Field(None, max_length=1024)
    enabled: bool = True
    severity_threshold: int = Field(default=400, ge=0, le=1000)
    conditions: List[AlertCondition] = Field(default=[])
    notifications: List[AlertNotification] = Field(default=[])
    cooldown_minutes: int = Field(default=1440, ge=0)  # 24 hours default


class AlertRuleUpdate(BaseModel):
    """Update alert rule payload."""
    name: Optional[str] = Field(None, min_length=1, max_length=256)
    description: Optional[str] = Field(None, max_length=1024)
    enabled: Optional[bool] = None
    severity_threshold: Optional[int] = Field(None, ge=0, le=1000)
    conditions: Optional[List[AlertCondition]] = None
    notifications: Optional[List[AlertNotification]] = None
    cooldown_minutes: Optional[int] = Field(None, ge=0)


class AlertResponse(BaseModel):
    """Public alert representation."""
    id: str
    title: str
    severity: str
    score: int
    status: str
    category: str
    source_type: str
    source_url: Optional[str] = None
    created_at: datetime
    acknowledged_by: Optional[str] = None
    summary: Optional[str] = None
    matched_keywords: Optional[List[str]] = None
    actor_pseudonym: Optional[str] = None
    actor_profile_id: Optional[str] = None


class AlertDetailResponse(BaseModel):
    """Detailed alert response."""
    id: str
    title: str
    severity: str
    score: int
    score_breakdown: Optional[Dict] = None
    status: str
    assignee: Optional[str] = None
    category: str
    source: Optional[Dict] = None
    content: Optional[Dict] = None
    entities: Optional[Dict] = None
    analysis: Optional[Dict] = None
    actor: Optional[Dict] = None
    timeline: Optional[List[Dict]] = None
    related_alerts: Optional[List[Dict]] = None
    created_at: datetime
    updated_at: datetime


class AlertUpdateRequest(BaseModel):
    """Update alert payload."""
    status: str = Field(..., pattern="^(new|acknowledged|investigating|resolved|false_positive)$")
    assignee: Optional[str] = None
    comment: Optional[str] = Field(None, max_length=2048)


class AlertBulkUpdateRequest(BaseModel):
    """Bulk update alerts."""
    alert_ids: List[str] = Field(..., min_length=1, max_length=100)
    action: str = Field(..., pattern="^(acknowledge|investigating|resolved|false_positive)$")
    assignee: Optional[str] = None


class AlertStatsResponse(BaseModel):
    """Alert statistics."""
    total: int
    by_severity: Dict[str, int]
    by_category: Dict[str, int]
    by_status: Dict[str, int]
    trend: List[Dict]


def new_alert_document(
    title: str,
    severity: str,
    score: int,
    category: str,
    source_url: str,
    source_type: str,
    content_id: str,
    matched_keywords: Optional[List[str]] = None,
    summary: Optional[str] = None,
    score_breakdown: Optional[Dict] = None,
    actor_pseudonym: Optional[str] = None,
    actor_profile_id: Optional[str] = None,
    entities: Optional[Dict] = None,
    analysis: Optional[Dict] = None,
) -> dict:
    """Create a new alert document for MongoDB."""
    now = datetime.now(timezone.utc)
    return {
        "_id": str(uuid.uuid4()),
        "title": title,
        "severity": severity,
        "score": score,
        "score_breakdown": score_breakdown or {},
        "status": "new",
        "category": category,
        "source_type": source_type,
        "source_url": source_url,
        "content_id": content_id,
        "summary": summary or "",
        "matched_keywords": matched_keywords or [],
        "actor_pseudonym": actor_pseudonym,
        "actor_profile_id": actor_profile_id,
        "assignee": None,
        "acknowledged_by": None,
        "comments": [],
        "entities": entities or {},
        "analysis": analysis or {},
        "timeline": [
            {"event": "alert_created", "timestamp": now.isoformat(), "detail": f"Alert triggered: {title}"},
        ],
        "related_alerts": [],
        "created_at": now,
        "updated_at": now,
    }
