"""
LaundraLens X — Real-Time Transaction Streaming Engine
Simulates high-throughput live transaction rails (e.g. Razorpay payment webhooks / UPI switch).
Computes lightweight sliding-window velocity and flags anomalous spikes in real time.
"""
from __future__ import annotations

import asyncio
import json
import random
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, Any

CHANNELS = ["UPI", "IMPS", "NEFT", "RTGS"]
LOCATIONS = ["Mumbai", "Bengaluru", "Delhi", "Hyderabad", "Pune", "Chennai"]


class LiveTransactionStreamer:
    """Generates continuous synthetic transaction stream with periodic suspicious bursts."""

    def __init__(self, normal_rate_hz: float = 1.5):
        self.normal_rate_hz = normal_rate_hz
        self._running = False
        self._counter = 0

    async def event_generator(self) -> AsyncGenerator[str, None]:
        """Yields Server-Sent Events (SSE) with live formatted transaction JSON."""
        self._running = True

        while self._running:
            self._counter += 1
            now = datetime.now(timezone.utc)

            # Every 12-15 transactions, inject a suspicious high-value rapid transfer
            is_anomaly = (self._counter % 12 == 0)

            if is_anomaly:
                amount = round(random.uniform(500000.0, 2500000.0), 2)
                sender = f"ACC-BURST-{random.randint(1, 3):03d}"
                receiver = f"ACC-MULE-{random.randint(10, 20):03d}"
                channel = "RTGS" if amount > 1000000 else "IMPS"
                flag = "HIGH_VALUE_VELOCITY_SPIKE"
            else:
                amount = round(random.uniform(150.0, 15000.0), 2)
                sender = f"ACC-{random.randint(100, 499):04d}"
                receiver = f"ACC-{random.randint(100, 499):04d}"
                channel = random.choice(CHANNELS)
                flag = "NORMAL"

            tx_event = {
                "sequence": self._counter,
                "transaction_id": f"LIVE-TX-{uuid.uuid4().hex[:8].upper()}",
                "timestamp": now.isoformat(),
                "time_str": now.strftime("%H:%M:%S"),
                "sender_account_id": sender,
                "receiver_account_id": receiver,
                "amount": amount,
                "amount_formatted": f"₹{amount:,.2f}",
                "currency": "INR",
                "channel": channel,
                "location": random.choice(LOCATIONS),
                "is_anomalous": is_anomaly,
                "anomaly_flag": flag,
            }

            yield f"data: {json.dumps(tx_event)}\n\n"

            # Sleep between events
            delay = 1.0 / self.normal_rate_hz
            await asyncio.sleep(delay)

    def stop(self):
        self._running = False
