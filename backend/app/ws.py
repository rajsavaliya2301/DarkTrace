"""WebSocket and SSE real-time event streams for live updates on alerts, actors, and content.

Provides:
  - WebSocket at /ws/events (general), /ws/alerts, /ws/content (specific)
  - SSE at /events/stream (Server-Sent Events for browsers)
  - Poll at /events/poll (for fallback)
"""

import asyncio
import json
import logging
import time
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, Request
from fastapi.responses import StreamingResponse

from app.pipeline import get_broadcaster

logger = logging.getLogger(__name__)

router = APIRouter()


# ─── Server-Sent Events (SSE) ──────────────────────────────────────────────


async def sse_generator(channels: list):
    """Generate SSE events for the given channels."""
    broadcaster = get_broadcaster()
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)

    for ch in channels:
        broadcaster.subscribe(ch, queue)

    try:
        # Send initial connection event
        yield f"data: {json.dumps({'type': 'connected', 'channels': channels})}\n\n"

        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield f"data: {json.dumps(event)}\n\n"
            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': time.time()})}\n\n"
    except asyncio.CancelledError:
        pass
    finally:
        for ch in channels:
            broadcaster.unsubscribe(ch, queue)


@router.get("/events/stream")
async def sse_events(
    request: Request,
    channels: str = Query("alert,dashboard", description="Comma-separated channels"),
):
    """Server-Sent Events endpoint for real-time updates (browser-friendly)."""
    ch_list = [ch.strip() for ch in channels.split(",") if ch.strip()]
    return StreamingResponse(
        sse_generator(ch_list),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ─── Polling Endpoint ──────────────────────────────────────────────────────


_latest_events: dict = {
    "content": [],
    "actor": [],
    "alert": [],
    "dashboard": [],
}


async def _poll_recorder():
    """Background task that records the latest events for polling clients."""
    broadcaster = get_broadcaster()
    for ch in ["content", "actor", "alert", "dashboard"]:
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        broadcaster.subscribe(ch, q)
        try:
            while True:
                event = await q.get()
                _latest_events[ch].append(event)
                # Keep only last 50 events per channel
                if len(_latest_events[ch]) > 50:
                    _latest_events[ch] = _latest_events[ch][-50:]
        except Exception:
            pass


# Start the poll recorder on module import
_poll_task: Optional[asyncio.Task] = None


def start_poll_recorder():
    """Start the background poll recorder (called from main.py lifespan)."""
    global _poll_task
    if _poll_task is None:
        _poll_task = asyncio.create_task(_poll_recorder())


@router.get("/events/poll")
async def poll_events(
    channel: str = Query("alert", description="Channel to poll"),
    since: Optional[float] = Query(None, description="Only return events after this timestamp"),
    limit: int = Query(10, ge=1, le=50),
):
    """Poll endpoint for real-time events (fallback if WebSocket/SSE not available).

    The frontend can poll this every few seconds to get new events.
    """
    events = _latest_events.get(channel, [])
    if since:
        events = [e for e in events if e.get("timestamp") and _ts(e) > since]
    return {
        "channel": channel,
        "events": events[-limit:],
        "count": len(events[-limit:]),
    }


def _ts(event: dict) -> float:
    """Extract timestamp from an event dict."""
    ts = event.get("timestamp", 0)
    if isinstance(ts, str):
        try:
            from datetime import datetime
            return datetime.fromisoformat(ts).timestamp()
        except Exception:
            return 0
    return float(ts) if ts else 0


# ─── WebSocket Endpoints ───────────────────────────────────────────────────


@router.websocket("/ws/events")
async def websocket_events(
    websocket: WebSocket,
    channels: str = Query("content,actor,alert,dashboard", description="Comma-separated channels to subscribe to"),
):
    """WebSocket endpoint for real-time event streaming.

    Channels: content, actor, alert, dashboard
    Subscribe to comma-separated channels via query param:
      ws://localhost:8000/v1/ws/events?channels=alert,actor
    """
    await websocket.accept()
    logger.info("WebSocket client connected (requested channels: %s)", channels)

    broadcaster = get_broadcaster()
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    subscribed_channels = [ch.strip() for ch in channels.split(",") if ch.strip() in broadcaster._subscribers]

    # Subscribe to requested channels
    for ch in subscribed_channels:
        broadcaster.subscribe(ch, queue)

    try:
        # Send initial subscription confirmation
        await websocket.send_json({
            "type": "connected",
            "channels": subscribed_channels,
            "subscriber_counts": broadcaster.subscriber_count,
        })

        while True:
            # Wait for events with a ping/heartbeat every 30s
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                await websocket.send_json(event)
            except asyncio.TimeoutError:
                # Send heartbeat
                try:
                    await websocket.send_json({"type": "heartbeat", "timestamp": __import__('time').time()})
                except Exception:
                    break

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.warning("WebSocket error: %s", e)
    finally:
        # Unsubscribe
        for ch in subscribed_channels:
            broadcaster.unsubscribe(ch, queue)
        logger.info("WebSocket client cleaned up (channels: %s)", subscribed_channels)


@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """Shortcut WebSocket that subscribes only to alert events."""
    await websocket.accept()
    broadcaster = get_broadcaster()
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    broadcaster.subscribe("alert", queue)

    try:
        await websocket.send_json({"type": "connected", "channel": "alert"})
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                await websocket.send_json(event)
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "heartbeat"})
    except WebSocketDisconnect:
        pass
    finally:
        broadcaster.unsubscribe("alert", queue)


@router.websocket("/ws/content")
async def websocket_content(websocket: WebSocket):
    """Shortcut WebSocket that subscribes only to content (search) events."""
    await websocket.accept()
    broadcaster = get_broadcaster()
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    broadcaster.subscribe("content", queue)

    try:
        await websocket.send_json({"type": "connected", "channel": "content"})
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                await websocket.send_json(event)
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "heartbeat"})
    except WebSocketDisconnect:
        pass
    finally:
        broadcaster.unsubscribe("content", queue)
