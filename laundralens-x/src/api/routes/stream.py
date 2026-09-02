"""
LaundraLens X — Real-time Transaction Streaming API Routes
Exposes Server-Sent Events (SSE) and snapshot endpoints for live transaction monitoring.
"""
from __future__ import annotations

import json
from collections import deque
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from src.stream.generator import LiveTransactionStreamer

router = APIRouter(prefix="/stream", tags=["stream"])

# Global streamer instance and recent circular buffer
_streamer = LiveTransactionStreamer(normal_rate_hz=2.0)
_recent_buffer: deque = deque(maxlen=50)


@router.get("/transactions")
async def stream_live_transactions():
    """
    Server-Sent Events (SSE) endpoint for continuous live transaction monitoring.
    Clients (browsers, dashboards, Kafka bridge) receive real-time JSON events.
    """
    async def sse_wrapper():
        async for event in _streamer.event_generator():
            # Cache in circular buffer for polling clients
            if event.startswith("data: "):
                try:
                    payload = json.loads(event[6:].strip())
                    _recent_buffer.appendleft(payload)
                except Exception:
                    pass
            yield event

    return StreamingResponse(
        sse_wrapper(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/recent")
def get_recent_streamed_events(limit: int = 15):
    """Returns the most recent live transactions from the sliding-window buffer."""
    events = list(_recent_buffer)[:limit]
    return {
        "count": len(events),
        "buffer_capacity": _recent_buffer.maxlen,
        "events": events,
    }
