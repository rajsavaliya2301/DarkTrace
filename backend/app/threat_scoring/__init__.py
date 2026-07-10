"""Threat scoring engine — computes severity scores for analyzed content."""

from app.threat_scoring.router import router as threat_scoring_router

__all__ = ["threat_scoring_router"]
