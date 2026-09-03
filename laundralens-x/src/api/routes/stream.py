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


def populate_buffer_sample(count: int = 10):
    """Seed buffer with immediate realistic transactions if empty."""
    import random, uuid
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    channels = ["UPI", "IMPS", "NEFT", "RTGS"]
    locations = ["Mumbai", "Bengaluru", "Delhi", "Hyderabad", "Pune"]
    for i in range(count):
        is_ano = (i == 2)
        amount = round(random.uniform(500000.0, 1800000.0), 2) if is_ano else round(random.uniform(250.0, 15000.0), 2)
        sender = "ACC-B-001" if is_ano else f"ACC-{random.randint(100, 400):04d}"
        receiver = f"ACC-C-{i:03d}" if is_ano else f"ACC-{random.randint(100, 400):04d}"
        t_time = now - timedelta(seconds=(count - i) * 12)
        _recent_buffer.appendleft({
            "sequence": i + 1,
            "transaction_id": f"LIVE-TX-{uuid.uuid4().hex[:8].upper()}",
            "timestamp": t_time.isoformat(),
            "time_str": t_time.strftime("%H:%M:%S"),
            "sender_account_id": sender,
            "receiver_account_id": receiver,
            "amount": amount,
            "amount_formatted": f"₹{amount:,.2f}",
            "currency": "INR",
            "channel": "RTGS" if amount > 500000 else random.choice(channels),
            "location": random.choice(locations),
            "is_anomalous": is_ano,
            "anomaly_flag": "HIGH_VALUE_VELOCITY_SPIKE" if is_ano else "NORMAL",
        })


@router.get("/recent")
def get_recent_streamed_events(limit: int = 15):
    """Returns the most recent live transactions from the sliding-window buffer."""
    if not _recent_buffer:
        populate_buffer_sample(10)
    events = list(_recent_buffer)[:limit]
    return {
        "count": len(events),
        "buffer_capacity": _recent_buffer.maxlen,
        "events": events,
    }
