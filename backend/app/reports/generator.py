"""Report generation engine — produces PDF, CSV, and JSON reports."""

import csv
import hashlib
import io
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.config import get_settings
from app.database import get_mongodb

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates reports in PDF, CSV, and JSON formats."""

    async def generate(self, report_id: str, report_type: str, format_type: str,
                       parameters: dict, created_by: str) -> dict:
        """Generate a report based on type and format."""
        settings = get_settings()
        db = await get_mongodb()

        # Collect data based on report type
        data = await self._collect_data(report_type, parameters)

        # Generate file
        if format_type == "pdf":
            file_path, file_size = await self._generate_pdf(report_id, report_type, data, parameters)
        elif format_type == "csv":
            file_path, file_size = await self._generate_csv(report_id, report_type, data, parameters)
        elif format_type == "json":
            file_path, file_size = await self._generate_json(report_id, report_type, data, parameters)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

        # Compute hash
        content_hash = ""
        try:
            with open(file_path, "rb") as f:
                content_hash = hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            logger.warning("Failed to compute hash for report %s: %s", report_id, e)

        # Update report document
        await db.reports.update_one(
            {"_id": report_id},
            {
                "$set": {
                    "status": "completed",
                    "file_path": file_path,
                    "file_size_bytes": file_size,
                    "content_hash": content_hash,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )

        return {
            "report_id": report_id,
            "status": "completed",
            "format": format_type,
            "file_size_bytes": file_size,
            "file_path": file_path,
        }

    async def _collect_data(self, report_type: str, parameters: dict) -> dict:
        """Collect data for the report."""
        db = await get_mongodb()

        if report_type == "alert_report":
            alert_id = parameters.get("alert_id")
            if not alert_id:
                raise ValueError("alert_id required for alert_report")
            alert = await db.alerts.find_one({"_id": alert_id})
            if not alert:
                raise ValueError(f"Alert {alert_id} not found")
            return {"alert": alert}

        elif report_type == "actor_dossier":
            actor_id = parameters.get("actor_id")
            if not actor_id:
                raise ValueError("actor_id required for actor_dossier")
            actor = await db.actor_profiles.find_one({"_id": actor_id})
            if not actor:
                raise ValueError(f"Actor {actor_id} not found")
            # Get related alerts
            alerts = await db.alerts.find(
                {"actor_profile_id": actor_id}
            ).sort("created_at", -1).limit(50).to_list(length=50)
            return {"actor": actor, "alerts": alerts}

        elif report_type == "trend_report":
            date_from = parameters.get("date_from")
            date_to = parameters.get("date_to")
            query = {}
            if date_from:
                query["created_at"] = query.get("created_at", {})
                query["created_at"]["$gte"] = datetime.fromisoformat(date_from)
            if date_to:
                query["created_at"] = query.get("created_at", {})
                query["created_at"]["$lte"] = datetime.fromisoformat(date_to)

            alerts = await db.alerts.find(query).sort("created_at", -1).limit(1000).to_list(length=1000)

            # Compute stats
            by_severity = {}
            by_category = {}
            for a in alerts:
                sev = a.get("severity", "unknown")
                by_severity[sev] = by_severity.get(sev, 0) + 1
                cat = a.get("category", "unknown")
                by_category[cat] = by_category.get(cat, 0) + 1

            return {
                "alerts": alerts,
                "stats": {
                    "total": len(alerts),
                    "by_severity": by_severity,
                    "by_category": by_category,
                },
                "date_from": date_from,
                "date_to": date_to,
            }

        elif report_type == "raw_export":
            filters = parameters.get("filters", {})
            query = {}
            if filters.get("source_type"):
                query["source_type"] = filters["source_type"]
            if filters.get("date_from"):
                query["fetch_timestamp"] = query.get("fetch_timestamp", {})
                query["fetch_timestamp"]["$gte"] = datetime.fromisoformat(filters["date_from"])
            if filters.get("date_to"):
                query["fetch_timestamp"] = query.get("fetch_timestamp", {})
                query["fetch_timestamp"]["$lte"] = datetime.fromisoformat(filters["date_to"])

            contents = await db.raw_content.find(query).limit(500).to_list(length=500)
            return {"contents": contents, "count": len(contents)}

        else:
            raise ValueError(f"Unsupported report type: {report_type}")

    async def _generate_pdf(self, report_id: str, report_type: str, data: dict, parameters: dict) -> tuple:
        """Generate PDF report using ReportLab."""
        settings = get_settings()
        os.makedirs(settings.REPORT_STORAGE_PATH, exist_ok=True)
        file_path = os.path.join(settings.REPORT_STORAGE_PATH, f"{report_id}.pdf")

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
            from reportlab.lib import colors

            doc = SimpleDocTemplate(file_path, pagesize=A4)
            styles = getSampleStyleSheet()
            elements = []

            # Title
            title_map = {
                "alert_report": "DarkTrace - Alert Report",
                "actor_dossier": "DarkTrace - Actor Dossier",
                "trend_report": "DarkTrace - Trend Report",
                "raw_export": "DarkTrace - Raw Data Export",
            }
            elements.append(Paragraph(title_map.get(report_type, "DarkTrace Report"), styles["Title"]))
            elements.append(Paragraph(f"Generated: {datetime.now(timezone.utc).isoformat()}", styles["Normal"]))
            elements.append(Spacer(1, 0.25 * inch))

            if report_type == "alert_report" and "alert" in data:
                alert = data["alert"]
                elements.append(Paragraph(f"Alert: {alert.get('title', 'N/A')}", styles["Heading1"]))
                elements.append(Paragraph(f"Severity: {alert.get('severity', 'N/A')}", styles["Normal"]))
                elements.append(Paragraph(f"Score: {alert.get('score', 0)}", styles["Normal"]))
                elements.append(Paragraph(f"Status: {alert.get('status', 'N/A')}", styles["Normal"]))
                elements.append(Paragraph(f"Source: {alert.get('source_url', 'N/A')}", styles["Normal"]))
                if alert.get("summary"):
                    elements.append(Paragraph(f"Summary: {alert['summary']}", styles["Normal"]))
                if alert.get("matched_keywords"):
                    elements.append(Paragraph(f"Keywords: {', '.join(alert['matched_keywords'])}", styles["Normal"]))

            elif report_type == "actor_dossier" and "actor" in data:
                actor = data["actor"]
                elements.append(Paragraph(f"Actor: {actor.get('name', 'Unknown')}", styles["Heading1"]))
                elements.append(Paragraph(f"Risk Score: {actor.get('risk_score', 0)}", styles["Normal"]))
                elements.append(Paragraph(f"Pseudonyms: {', '.join(actor.get('pseudonyms', []))}", styles["Normal"]))
                elements.append(Paragraph(f"Total Posts: {actor.get('total_posts', 0)}", styles["Normal"]))
                elements.append(Paragraph(f"First Seen: {str(actor.get('first_seen', ''))}", styles["Normal"]))
                elements.append(Paragraph(f"Last Seen: {str(actor.get('last_seen', ''))}", styles["Normal"]))

                if data.get("alerts"):
                    elements.append(Spacer(1, 0.25 * inch))
                    elements.append(Paragraph("Related Alerts:", styles["Heading2"]))
                    for alert in data["alerts"][:20]:
                        elements.append(Paragraph(
                            f"- {alert.get('title', '')} ({alert.get('severity', '')})",
                            styles["Normal"],
                        ))

            elif report_type == "trend_report":
                stats = data.get("stats", {})
                elements.append(Paragraph(f"Total Alerts: {stats.get('total', 0)}", styles["Normal"]))
                elements.append(Spacer(1, 0.2 * inch))
                elements.append(Paragraph("By Severity:", styles["Heading2"]))
                for sev, count in stats.get("by_severity", {}).items():
                    elements.append(Paragraph(f"  {sev}: {count}", styles["Normal"]))
                elements.append(Spacer(1, 0.2 * inch))
                elements.append(Paragraph("By Category:", styles["Heading2"]))
                for cat, count in stats.get("by_category", {}).items():
                    elements.append(Paragraph(f"  {cat}: {count}", styles["Normal"]))

            elif report_type == "raw_export" and "contents" in data:
                elements.append(Paragraph(f"Total Items: {data.get('count', 0)}", styles["Normal"]))

            doc.build(elements)
            file_size = os.path.getsize(file_path)
            logger.info("PDF report generated: %s (%d bytes)", file_path, file_size)
            return file_path, file_size

        except ImportError:
            logger.warning("ReportLab not available. Generating text file instead.")
            return await self._generate_txt_fallback(data, file_path, report_type, parameters)

    async def _generate_txt_fallback(self, data: dict, file_path: str, report_type: str, parameters: dict) -> tuple:
        """Fallback text report when ReportLab is not available."""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"DarkTrace Report - {report_type}\n")
            f.write(f"Generated: {datetime.now(timezone.utc).isoformat()}\n")
            f.write("=" * 60 + "\n\n")

            if report_type == "alert_report" and "alert" in data:
                alert = data["alert"]
                for key, value in alert.items():
                    if key not in ("_id", "timeline", "entities", "analysis"):
                        f.write(f"{key}: {value}\n")
            elif report_type == "trend_report" and "stats" in data:
                stats = data["stats"]
                f.write(json.dumps(stats, indent=2, default=str))
            elif report_type == "raw_export" and "contents" in data:
                for item in data["contents"]:
                    item["_id"] = str(item["_id"])
                    if "raw_html" in item:
                        item["raw_html"] = item["raw_html"][:1000]
                    f.write(json.dumps(item, default=str) + "\n")

        file_size = os.path.getsize(file_path)
        return file_path, file_size

    async def _generate_csv(self, report_id: str, report_type: str, data: dict, parameters: dict) -> tuple:
        """Generate CSV report."""
        settings = get_settings()
        os.makedirs(settings.REPORT_STORAGE_PATH, exist_ok=True)
        file_path = os.path.join(settings.REPORT_STORAGE_PATH, f"{report_id}.csv")

        if report_type == "alert_report" and "alert" in data:
            alert = data["alert"]
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Field", "Value"])
                for key in ["title", "severity", "score", "status", "category", "source_url", "source_type", "summary"]:
                    writer.writerow([key, alert.get(key, "")])

        elif report_type == "trend_report" and "alerts" in data:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Title", "Severity", "Score", "Status", "Category", "Created At"])
                for alert in data["alerts"]:
                    writer.writerow([
                        alert.get("_id", ""),
                        alert.get("title", ""),
                        alert.get("severity", ""),
                        alert.get("score", 0),
                        alert.get("status", ""),
                        alert.get("category", ""),
                        alert.get("created_at", ""),
                    ])

        elif report_type == "raw_export" and "contents" in data:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["URL", "Source Type", "Site", "HTTP Status", "Content Hash", "Fetched At"])
                for content in data["contents"]:
                    writer.writerow([
                        content.get("url", ""),
                        content.get("source_type", ""),
                        content.get("site_name", ""),
                        content.get("http_status", 0),
                        content.get("content_hash", ""),
                        content.get("fetch_timestamp", ""),
                    ])

        else:
            # Generic JSON-to-CSV
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                f.write(json.dumps(data, default=str))

        file_size = os.path.getsize(file_path)
        logger.info("CSV report generated: %s (%d bytes)", file_path, file_size)
        return file_path, file_size

    async def _generate_json(self, report_id: str, report_type: str, data: dict, parameters: dict) -> tuple:
        """Generate JSON report."""
        settings = get_settings()
        os.makedirs(settings.REPORT_STORAGE_PATH, exist_ok=True)
        file_path = os.path.join(settings.REPORT_STORAGE_PATH, f"{report_id}.json")

        # Remove raw_html from content to keep file size manageable
        if "contents" in data:
            for item in data["contents"]:
                if "raw_html" in item:
                    item["raw_html"] = item["raw_html"][:500] if item.get("raw_html") else ""
                item["_id"] = str(item["_id"])

        if "alert" in data:
            data["alert"]["_id"] = str(data["alert"]["_id"])
            if "timeline" in data["alert"]:
                data["alert"]["timeline"] = [str(t) if not isinstance(t, dict) else t for t in data["alert"]["timeline"]]

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        file_size = os.path.getsize(file_path)
        logger.info("JSON report generated: %s (%d bytes)", file_path, file_size)
        return file_path, file_size

    async def get_download_url(self, report_id: str) -> Optional[str]:
        """Get a secure download URL for the report."""
        db = await get_mongodb()
        report = await db.reports.find_one({"_id": report_id})
        if not report:
            return None

        from app.config import get_settings
        settings = get_settings()

        # Generate temporary download token
        import secrets
        token = secrets.token_urlsafe(32)
        expiry = datetime.now(timezone.utc)
        from datetime import timedelta
        expiry += timedelta(hours=settings.REPORT_EXPIRY_HOURS)

        await db.reports.update_one(
            {"_id": report_id},
            {"$set": {"download_token": token, "expires_at": expiry}},
        )

        return f"/v1/reports/{report_id}/download?token={token}"


# Singleton
_report_generator: Optional[ReportGenerator] = None


async def get_report_generator() -> ReportGenerator:
    """Get or create the singleton report generator."""
    global _report_generator
    if _report_generator is None:
        _report_generator = ReportGenerator()
    return _report_generator
