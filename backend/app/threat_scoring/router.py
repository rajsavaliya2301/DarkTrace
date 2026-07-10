"""Threat scoring API endpoints — score content, view/update rules."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.dependencies import (
    get_current_user,
    CurrentUser,
    require_permission,
    require_role,
    log_user_action,
)
from app.threat_scoring.engine import get_scoring_engine
from app.threat_scoring.rules import get_scoring_rules

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/threat-scoring", tags=["Threat Scoring"])


# ─── Pydantic Schemas ──────────────────────────────────────────────────────────


class ScoreContentRequest(BaseModel):
    """Request to score analyzed content."""
    content_id: str = Field(..., description="Content identifier")
    classification: dict = Field(default_factory=dict, description="Threat classification results")
    entities: dict = Field(default_factory=dict, description="Extracted entities")
    sentiment: dict = Field(default_factory=dict, description="Sentiment analysis results")
    keyword_matches: dict = Field(default_factory=dict, description="Keyword matching results")
    published_date: Optional[str] = Field(default=None, description="Content publish date (ISO format)")
    site_name: str = Field(default="unknown", max_length=256)
    source_type: str = Field(default="onion", pattern="^(onion|i2p|surface)$")
    actor_risk_score: Optional[int] = Field(default=None, ge=0, le=1000)


class UpdateWeightsRequest(BaseModel):
    """Update scoring weights (admin only)."""
    weights: dict = Field(..., description="New weight values for scoring factors")


class ScoringRuleResponse(BaseModel):
    """Scoring rules and weights."""
    weights: dict
    severity_thresholds: dict
    classification_scores: dict


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/score", response_model=dict)
async def score_content(
    request: Request,
    body: ScoreContentRequest,
    current_user: CurrentUser = Depends(require_permission("search:read")),
):
    """Compute a threat severity score (0-1000) for analyzed content."""
    engine = await get_scoring_engine()
    result = await engine.score(
        content_id=body.content_id,
        classification=body.classification,
        entities=body.entities,
        sentiment=body.sentiment,
        keyword_matches=body.keyword_matches,
        published_date=body.published_date,
        site_name=body.site_name,
        source_type=body.source_type,
        actor_risk_score=body.actor_risk_score,
    )

    await log_user_action(
        request, current_user, "threat_score", "content", body.content_id,
        details={"score": result.get("score"), "severity": result.get("severity")},
    )

    return result


@router.get("/rules", response_model=ScoringRuleResponse)
async def get_scoring_rules_endpoint(
    current_user: CurrentUser = Depends(require_permission("search:read")),
):
    """Get current scoring rules, weights, and severity thresholds."""
    rules = get_scoring_rules()
    return ScoringRuleResponse(
        weights=rules.get_weights(),
        severity_thresholds=rules.SEVERITY_THRESHOLDS,
        classification_scores=rules.CLASSIFICATION_SCORES,
    )


@router.put("/rules", response_model=ScoringRuleResponse)
async def update_scoring_weights(
    request: Request,
    body: UpdateWeightsRequest,
    current_user: CurrentUser = Depends(require_role("admin")),
):
    """Update scoring weights (admin only)."""
    settings = request.app.state  # Not ideal — use config override instead
    from app.config import get_settings as cfg

    # Validate weights sum to ~1.0
    total = sum(body.weights.values())
    if abs(total - 1.0) > 0.01:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Weights must sum to approximately 1.0 (got {total:.2f})",
        )

    # For now, log the update; weights are set via env var THREAT_SCORE_WEIGHTS
    logger.info("Scoring weights update requested by %s: %s", current_user.email, body.weights)

    # Re-initialize rules with new weights
    import json
    import os
    os.environ["THREAT_SCORE_WEIGHTS"] = json.dumps(body.weights)

    # Clear cached settings
    cfg.cache_clear()

    rules = get_scoring_rules()
    return ScoringRuleResponse(
        weights=rules.get_weights(),
        severity_thresholds=rules.SEVERITY_THRESHOLDS,
        classification_scores=rules.CLASSIFICATION_SCORES,
    )
