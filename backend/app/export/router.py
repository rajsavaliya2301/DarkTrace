"""Export and SIEM integration router — syslog, webhook, blockchain sealing."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.dependencies import (
    get_db,
    get_current_user,
    CurrentUser,
    require_permission,
    log_user_action,
)
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.export.siem import get_siem_exporter
from app.export.blockchain import get_blockchain_sealer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["Export & SIEM"])


# ─── Pydantic Schemas ──────────────────────────────────────────────────────────


class SIEMWebhookRequest(BaseModel):
    """Send alert to SIEM via webhook."""
    endpoint: str = Field(..., description="SIEM webhook URL")
    alert_id: str = Field(..., description="Alert ID to export")
    format_type: str = Field(default="cef", pattern="^(cef|leef|json)$")
    api_key: str = Field(default="", description="Optional API key for SIEM")


class SIEMSyslogRequest(BaseModel):
    """Send alert to SIEM via syslog."""
    alert_id: str = Field(..., description="Alert ID to export")
    format_type: str = Field(default="cef", pattern="^(cef|leef|json)$")
    host: Optional[str] = Field(default=None, description="Syslog server host (default from config)")
    port: Optional[int] = Field(default=None, description="Syslog server port (default from config)")


class BlockchainSealRequest(BaseModel):
    """Seal a report hash to the blockchain."""
    report_id: str = Field(..., description="Report ID to seal")
    content_hash: str = Field(..., min_length=32, max_length=128, description="SHA-256 content hash")


class BlockchainVerifyRequest(BaseModel):
    """Verify a blockchain seal."""
    content_hash: str = Field(..., min_length=32, max_length=128, description="SHA-256 content hash to verify")


class ExportResponse(BaseModel):
    """Standard export response."""
    success: bool
    message: str
    details: Optional[dict] = None


# ─── SIEM Endpoints ───────────────────────────────────────────────────────────


@router.post("/siem/webhook", response_model=ExportResponse)
async def export_siem_webhook(
    request: Request,
    body: SIEMWebhookRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("export:write")),
):
    """Export an alert to a SIEM system via webhook (CEF/LEEF/JSON)."""
    # Fetch alert
    alert = await db.alerts.find_one({"_id": body.alert_id})
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    exporter = await get_siem_exporter()
    result = await exporter.send_webhook(
        endpoint=body.endpoint,
        alert=alert,
        api_key=body.api_key,
        format_type=body.format_type,
    )

    await log_user_action(
        request, current_user, "export_siem_webhook", "alert", body.alert_id,
        details={
            "endpoint": body.endpoint,
            "format": body.format_type,
            "status": result.get("status"),
        },
    )

    return ExportResponse(
        success=result.get("success", False),
        message=result.get("message", "Webhook sent"),
        details=result,
    )


@router.post("/siem/syslog", response_model=ExportResponse)
async def export_siem_syslog(
    request: Request,
    body: SIEMSyslogRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("export:write")),
):
    """Export an alert to a SIEM system via syslog (CEF/LEEF/JSON)."""
    from app.config import get_settings
    settings = get_settings()

    # Fetch alert
    alert = await db.alerts.find_one({"_id": body.alert_id})
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    host = body.host or settings.SIEM_SYSLOG_HOST
    port = body.port or settings.SIEM_SYSLOG_PORT

    if not host:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Syslog host not configured. Set SIEM_SYSLOG_HOST or provide host in request.",
        )

    exporter = await get_siem_exporter()
    result = await exporter.send_syslog(
        host=host,
        port=port,
        alert=alert,
        format_type=body.format_type,
    )

    await log_user_action(
        request, current_user, "export_siem_syslog", "alert", body.alert_id,
        details={
            "host": host,
            "port": port,
            "format": body.format_type,
            "status": result.get("status"),
        },
    )

    return ExportResponse(
        success=result.get("success", False),
        message=result.get("message", "Syslog sent"),
        details=result,
    )


# ─── Blockchain Endpoints ─────────────────────────────────────────────────────


@router.post("/blockchain/seal", response_model=ExportResponse)
async def export_blockchain_seal(
    request: Request,
    body: BlockchainSealRequest,
    current_user: CurrentUser = Depends(require_permission("export:write")),
):
    """Seal a report's content hash to the blockchain for tamper-proof evidence."""
    sealer = await get_blockchain_sealer()
    result = await sealer.seal_report(
        report_id=body.report_id,
        content_hash=body.content_hash,
    )

    await log_user_action(
        request, current_user, "blockchain_seal", "report", body.report_id,
        details={
            "chain": result.get("chain", "unknown"),
            "tx_hash": result.get("tx_hash", ""),
        },
    )

    return ExportResponse(
        success=True,
        message=f"Report sealed on {result.get('chain', 'unknown')} blockchain",
        details=result,
    )


@router.post("/blockchain/verify", response_model=ExportResponse)
async def export_blockchain_verify(
    request: Request,
    body: BlockchainVerifyRequest,
    current_user: CurrentUser = Depends(require_permission("export:write")),
):
    """Verify if a content hash exists on the blockchain."""
    sealer = await get_blockchain_sealer()
    result = await sealer.verify_seal(content_hash=body.content_hash)

    return ExportResponse(
        success=result.get("exists", False),
        message="Seal verified" if result.get("exists") else "No seal found for this hash",
        details=result,
    )
