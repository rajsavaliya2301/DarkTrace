"""SIEM integration — CEF/LEEF format generation, syslog dispatch, webhook forwarding."""

import asyncio
import json
import logging
import socket
from datetime import datetime, timezone
from typing import Dict, List, Optional

import aiohttp

from app.config import get_settings

logger = logging.getLogger(__name__)


class SIEMExporter:
    """Exports alerts to SIEM systems via webhook or syslog."""

    async def send_webhook(self, endpoint: str, alert: dict, api_key: str = "", format_type: str = "cef") -> dict:
        """Send alert to SIEM webhook endpoint."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "DarkTrace-SIEM-Exporter/1.0",
        }
        if api_key:
            headers["X-API-Key"] = api_key

        if format_type == "cef":
            payload = self._format_cef(alert)
            headers["Content-Type"] = "text/plain"
        elif format_type == "leef":
            payload = self._format_leef(alert)
            headers["Content-Type"] = "text/plain"
        else:
            payload = json.dumps(self._format_json(alert), indent=2)
            headers["Content-Type"] = "application/json"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    data=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    text = await response.text()
                    logger.info("SIEM webhook sent to %s: %s", endpoint, response.status)
                    return {
                        "status": response.status,
                        "message": text[:200],
                        "success": 200 <= response.status < 300,
                    }
        except asyncio.TimeoutError:
            logger.warning("SIEM webhook timeout for %s", endpoint)
            return {"status": 0, "message": "timeout", "success": False}
        except Exception as e:
            logger.warning("SIEM webhook failed for %s: %s", endpoint, e)
            return {"status": 0, "message": str(e), "success": False}

    async def send_syslog(self, host: str, port: int, alert: dict, format_type: str = "cef") -> dict:
        """Send alert via syslog (UDP)."""
        if format_type == "cef":
            message = self._format_cef(alert)
        elif format_type == "leef":
            message = self._format_leef(alert)
        else:
            message = json.dumps(self._format_json(alert))

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)
            sock.sendto(message.encode("utf-8"), (host, port))
            sock.close()
            logger.info("Syslog message sent to %s:%d", host, port)
            return {"status": 200, "message": "sent", "success": True}
        except Exception as e:
            logger.warning("Syslog send failed: %s", e)
            return {"status": 0, "message": str(e), "success": False}

    def _format_cef(self, alert: dict) -> str:
        """Format alert as CEF (Common Event Format)."""
        # CEF:0|Vendor|Product|Version|SignatureID|Name|Severity|Extension
        score = alert.get("score", 0)
        severity = alert.get("severity", "low")

        # Map severity to CEF severity (0-10)
        cef_severity = {
            "informational": 1,
            "low": 3,
            "medium": 5,
            "high": 8,
            "critical": 10,
        }.get(severity, 5)

        title = alert.get("title", "DarkTrace Alert")
        # Clean title for CEF (escape pipes)
        title = title.replace("|", "/").replace("\\", "\\\\")

        extension_parts = [
            f"dvc={self._get_hostname()}",
            f"start={datetime.now(timezone.utc).strftime('%b %d %Y %H:%M:%S')}",
            f"msg={title}",
            f"src={alert.get('source_url', 'unknown')}",
            f"suser={alert.get('actor_pseudonym', 'unknown')}",
            f"cs1Label=category cs1={alert.get('category', 'unknown')}",
            f"cs2Label=score cs2={score}",
            f"cs3Label=sourceType cs3={alert.get('source_type', 'unknown')}",
            f"cs4Label=status cs4={alert.get('status', 'new')}",
        ]

        if alert.get("matched_keywords"):
            keywords = ",".join(alert["matched_keywords"][:10])
            extension_parts.append(f"cs5Label=matchedKeywords cs5={keywords}")

        extension = " ".join(extension_parts)

        return f"CEF:0|DarkTrace|ThreatIntelligence|1.0|{score}|{title}|{cef_severity}|{extension}"

    def _format_leef(self, alert: dict) -> str:
        """Format alert as LEEF (Log Event Extended Format)."""
        # LEEF:1.0|Vendor|Product|Version|EventID|Attributes
        score = alert.get("score", 0)
        title = alert.get("title", "DarkTrace Alert").replace("|", "/").replace("\\", "\\\\")
        severity = alert.get("severity", "low")

        attrs = {
            "devTime": datetime.now(timezone.utc).strftime("%b %d %Y %H:%M:%S"),
            "title": title,
            "sourceUrl": alert.get("source_url", ""),
            "sourceType": alert.get("source_type", ""),
            "category": alert.get("category", ""),
            "score": str(score),
            "severity": severity,
            "status": alert.get("status", ""),
            "actor": alert.get("actor_pseudonym", ""),
        }

        attr_str = "\t".join([f"{k}={v}" for k, v in attrs.items() if v])
        return f"LEEF:1.0|DarkTrace|ThreatIntelligence|1.0|{score}|{attr_str}"

    def _format_json(self, alert: dict) -> dict:
        """Format alert as simple JSON."""
        return {
            "source": "DarkTrace",
            "type": "threat_alert",
            "version": "1.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "alert": {
                "id": alert.get("_id") or alert.get("id", ""),
                "title": alert.get("title", ""),
                "severity": alert.get("severity", ""),
                "score": alert.get("score", 0),
                "category": alert.get("category", ""),
                "source_url": alert.get("source_url", ""),
                "source_type": alert.get("source_type", ""),
                "status": alert.get("status", ""),
                "actor": alert.get("actor_pseudonym", ""),
                "matched_keywords": alert.get("matched_keywords", []),
                "created_at": alert.get("created_at", ""),
            },
        }

    def _get_hostname(self) -> str:
        """Get hostname for CEF header."""
        try:
            return socket.gethostname()
        except Exception:
            return "darktrace-server"


# Singleton
_siem_exporter: Optional[SIEMExporter] = None


async def get_siem_exporter() -> SIEMExporter:
    """Get or create the singleton SIEM exporter."""
    global _siem_exporter
    if _siem_exporter is None:
        _siem_exporter = SIEMExporter()
    return _siem_exporter
