"""Reports API endpoints — generate, list, download."""

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from app.reports.generator import get_report_generator
from app.dependencies import (
    get_db,
    get_current_user,
    CurrentUser,
    require_permission,
    log_user_action,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["Reports"])


class ReportGenerateRequest(BaseModel):
    type: str = Field(..., pattern="^(alert_report|actor_dossier|trend_report|raw_export)$")
    format: str = Field(default="pdf", pattern="^(pdf|csv|json)$")
    parameters: dict = Field(default={})


class ReportFromSearchRequest(BaseModel):
    """Generate a report from current search results."""
    query: str = Field(..., min_length=1, max_length=500)
    filters: Optional[dict] = Field(default=None)
    format: str = Field(default="pdf", pattern="^(pdf|csv|json)$")
    include_evidence: bool = Field(default=True)


class ReportResponse(BaseModel):
    id: str
    type: str
    format: str
    status: str
    file_size_bytes: Optional[int] = None
    download_url: Optional[str] = None
    url_expires_at: Optional[datetime] = None
    created_at: datetime
    blockchain_tx: Optional[dict] = None


@router.post("", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def generate_report(
    request: Request,
    body: ReportGenerateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("reports:create")),
):
    """Generate a new report."""
    import uuid
    report_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    # Create report document
    report_doc = {
        "_id": report_id,
        "type": body.type,
        "format": body.format,
        "status": "generating",
        "parameters": body.parameters,
        "file_path": None,
        "file_size_bytes": None,
        "content_hash": None,
        "digital_signature": None,
        "blockchain_tx": None,
        "download_token": None,
        "download_count": 0,
        "expires_at": None,
        "created_by": current_user.id,
        "created_at": now,
        "updated_at": now,
    }
    await db.reports.insert_one(report_doc)

    # Generate report in background
    asyncio.create_task(
        _generate_report_background(report_id, body.type, body.format, body.parameters, current_user.id)
    )

    await log_user_action(
        request, current_user, "report_generated", "report", report_id,
        details={"type": body.type, "format": body.format},
    )

    return {
        "report_id": report_id,
        "status": "generating",
        "estimated_completion": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/from-search", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def generate_report_from_search(
    request: Request,
    body: ReportFromSearchRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("reports:create")),
):
    """Generate a report from current search results (raw_export type)."""
    import uuid
    report_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    parameters = {
        "query": body.query,
        "filters": body.filters or {},
        "include_evidence": body.include_evidence,
    }

    report_doc = {
        "_id": report_id,
        "type": "raw_export",
        "format": body.format,
        "status": "generating",
        "parameters": parameters,
        "file_path": None,
        "file_size_bytes": None,
        "content_hash": None,
        "digital_signature": None,
        "blockchain_tx": None,
        "download_token": None,
        "download_count": 0,
        "expires_at": None,
        "created_by": current_user.id,
        "created_at": now,
        "updated_at": now,
    }
    await db.reports.insert_one(report_doc)

    # Trigger background generation — queries ES and packages results
    asyncio.create_task(
        _generate_from_search_background(
            report_id, body.query, body.filters, body.format, body.include_evidence, current_user.id
        )
    )

    await log_user_action(
        request, current_user, "report_generated_from_search", "report", report_id,
        details={"format": body.format, "query": body.query},
    )

    return {
        "report_id": report_id,
        "status": "generating",
    }


@router.get("", response_model=dict)
async def list_reports(
    page: int = 1,
    per_page: int = 25,
    type_filter: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("reports:read")),
):
    """List generated reports."""
    query = {}
    if type_filter:
        query["type"] = type_filter

    total = await db.reports.count_documents(query)
    cursor = (
        db.reports.find(query)
        .sort("created_at", -1)
        .skip((page - 1) * per_page)
        .limit(per_page)
    )
    reports = await cursor.to_list(length=per_page)

    data = []
    for r in reports:
        download_url = None
        url_expires_at = None
        if r.get("download_token") and r.get("expires_at"):
            if r["expires_at"] > datetime.now(timezone.utc):
                download_url = f"/v1/reports/{r['_id']}/download?token={r['download_token']}"
                url_expires_at = r["expires_at"]

        data.append(
            ReportResponse(
                id=str(r["_id"]),
                type=r.get("type", ""),
                format=r.get("format", "pdf"),
                status=r.get("status", "unknown"),
                file_size_bytes=r.get("file_size_bytes"),
                download_url=download_url,
                url_expires_at=url_expires_at,
                created_at=r.get("created_at", datetime.now(timezone.utc)),
                blockchain_tx=r.get("blockchain_tx"),
            )
        )

    return {
        "data": data,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": max(1, (total + per_page - 1) // per_page),
        },
    }


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("reports:read")),
):
    """Get report status and details."""
    report = await db.reports.find_one({"_id": report_id})
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    download_url = None
    url_expires_at = None
    if report.get("download_token") and report.get("expires_at"):
        if report["expires_at"] > datetime.now(timezone.utc):
            download_url = f"/v1/reports/{report_id}/download?token={report['download_token']}"
            url_expires_at = report["expires_at"]

    return ReportResponse(
        id=str(report["_id"]),
        type=report.get("type", ""),
        format=report.get("format", "pdf"),
        status=report.get("status", "unknown"),
        file_size_bytes=report.get("file_size_bytes"),
        download_url=download_url,
        url_expires_at=url_expires_at,
        created_at=report.get("created_at", datetime.now(timezone.utc)),
        blockchain_tx=report.get("blockchain_tx"),
    )


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    token: str = "",
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: Optional[CurrentUser] = Depends(get_current_user),
):
    """Download a generated report file."""
    report = await db.reports.find_one({"_id": report_id})
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    if report.get("status") != "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Report not yet completed")

    # Verify download token
    stored_token = report.get("download_token", "")
    if not stored_token or stored_token != token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid download token")

    # Check expiry
    expires_at = report.get("expires_at")
    if expires_at and expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Download link expired")

    file_path = report.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report file not found")

    # Increment download count
    await db.reports.update_one({"_id": report_id}, {"$inc": {"download_count": 1}})

    media_types = {
        "pdf": "application/pdf",
        "csv": "text/csv",
        "json": "application/json",
    }
    media_type = media_types.get(report.get("format", "pdf"), "application/octet-stream")
    filename = f"darktrace_report_{report_id[:8]}.{report.get('format', 'pdf')}"

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename,
    )


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    request: Request,
    report_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("reports:read")),
):
    """Delete a report and its associated file."""
    report = await db.reports.find_one({"_id": report_id})
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    # Remove the file if it exists
    file_path = report.get("file_path")
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError as e:
            logger.warning("Failed to remove report file %s: %s", file_path, e)

    await db.reports.delete_one({"_id": report_id})

    await log_user_action(
        request, current_user, "report_deleted", "report", report_id,
    )

    return None


async def _generate_report_background(report_id: str, report_type: str, format_type: str, parameters: dict, user_id: str):
    """Background task to generate a report."""
    try:
        generator = await get_report_generator()
        result = await generator.generate(report_id, report_type, format_type, parameters, user_id)
        logger.info("Report %s generated successfully: %s", report_id, result)
    except Exception as e:
        logger.error("Report %s generation failed: %s", report_id, e)
        try:
            db = await get_db()
            await db.reports.update_one(
                {"_id": report_id},
                {"$set": {"status": "failed", "updated_at": datetime.now(timezone.utc)}},
            )
        except Exception:
            pass


async def _generate_from_search_background(
    report_id: str,
    query: str,
    filters: Optional[dict],
    format_type: str,
    include_evidence: bool,
    user_id: str,
):
    """Background task: run ES search and generate a raw_export report from results."""
    try:
        from app.database import get_elasticsearch
        from app.config import get_settings

        es = await get_elasticsearch()

        # Build ES query
        es_must = [
            {
                "multi_match": {
                    "query": query,
                    "fields": ["title^3", "content_text^2", "author^2"],
                    "fuzziness": "AUTO",
                    "minimum_should_match": "70%",
                }
            }
        ]
        es_filter = []
        if filters:
            if filters.get("source_type"):
                es_filter.append({"term": {"source_type": filters["source_type"]}})
            if filters.get("category"):
                es_filter.append({"term": {"document_type": filters["category"]}})
            if filters.get("language"):
                es_filter.append({"term": {"language": filters["language"]}})

        es_query = {"bool": {"must": es_must}}
        if es_filter:
            es_query["bool"]["filter"] = es_filter

        response = await es.search(
            index="crawled_content",
            body={
                "query": es_query,
                "size": 500,
                "sort": ["_score"],
            },
        )
        hits = response["hits"]["hits"]
        total = response["hits"]["total"]["value"]

        # Package results into raw_export data
        contents = []
        for hit in hits:
            src = hit["_source"]
            entry = {
                "id": hit["_id"],
                "url": src.get("url", ""),
                "title": src.get("title", ""),
                "content_text": (src.get("content_text") or "")[:2000] if include_evidence else "",
                "author": src.get("author", ""),
                "source_type": src.get("source_type", ""),
                "site_name": src.get("site_name", ""),
                "document_type": src.get("document_type", ""),
                "language": src.get("language", ""),
                "crawl_timestamp": src.get("crawl_timestamp", ""),
                "score": hit.get("_score", 0),
                "entities": src.get("entities", {}),
            }
            if include_evidence and src.get("raw_html"):
                entry["raw_html"] = src["raw_html"][:1000]
            contents.append(entry)

        data = {
            "contents": contents,
            "count": total,
            "query": query,
            "filters": filters or {},
            "include_evidence": include_evidence,
        }

        # Write report file using the generator's file-writing methods
        settings = get_settings()
        import os, json, hashlib
        os.makedirs(settings.REPORT_STORAGE_PATH, exist_ok=True)

        if format_type == "json":
            file_path = os.path.join(settings.REPORT_STORAGE_PATH, f"{report_id}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
        elif format_type == "csv":
            import csv
            file_path = os.path.join(settings.REPORT_STORAGE_PATH, f"{report_id}.csv")
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "URL", "Title", "Author", "Source Type", "Site", "Language", "Crawled At", "Score"])
                for item in contents:
                    writer.writerow([
                        item["id"], item["url"], item["title"], item["author"],
                        item["source_type"], item["site_name"], item["language"],
                        item["crawl_timestamp"], item["score"],
                    ])
        else:  # pdf or fallback
            file_path = os.path.join(settings.REPORT_STORAGE_PATH, f"{report_id}.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"DarkTrace Search Export\n")
                f.write(f"Query: {query}\n")
                f.write(f"Generated: {datetime.now(timezone.utc).isoformat()}\n")
                f.write(f"Total Results: {total}\n")
                f.write("=" * 60 + "\n\n")
                for i, item in enumerate(contents, 1):
                    f.write(f"{i}. {item['title']}\n")
                    f.write(f"   URL: {item['url']}\n")
                    f.write(f"   Source: {item['source_type']} | {item['site_name']}\n")
                    f.write(f"   Score: {item['score']}\n")
                    if include_evidence and item.get("content_text"):
                        f.write(f"   Snippet: {item['content_text'][:300]}\n")
                    f.write("\n")

        file_size = os.path.getsize(file_path)

        # Compute content hash
        content_hash = ""
        try:
            with open(file_path, "rb") as f:
                content_hash = hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            logger.warning("Failed to compute hash for report %s: %s", report_id, e)

        # Update report document
        db = await get_db()
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

        logger.info("Report %s from search generated successfully (%d bytes)", report_id, file_size)

    except Exception as e:
        logger.error("Report %s from search generation failed: %s", report_id, e)
        try:
            db = await get_db()
            await db.reports.update_one(
                {"_id": report_id},
                {"$set": {"status": "failed", "updated_at": datetime.now(timezone.utc)}},
            )
        except Exception:
            pass
