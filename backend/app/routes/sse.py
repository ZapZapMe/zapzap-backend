# routes/sse.py
import json
import logging
from asyncio import Queue, sleep
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

cleanup_task = None

router = APIRouter(prefix="/sse", tags=["sse"])


class Connection:
    def __init__(self, queue: Queue):
        self.queue: Queue = queue
        self.connected_at: datetime = datetime.now()


# Payment hash -> list of active connections
connections: Dict[str, List[Connection]] = {}


@router.get("/subscribe")
async def subscribe_to_payment(request: Request, payment_hash: str):
    if not payment_hash:
        raise HTTPException(status_code=400, detail="Payment hash is required")

    q = Queue()
    connection = Connection(q)

    if payment_hash not in connections:
        connections[payment_hash] = []
    connections[payment_hash].append(connection)

    logging.info(f"New client connected to payment_hash={payment_hash}")

    async def event_stream():
        try:
            # Send initial connection confirmation
            message = json.dumps(
                {"payment_hash": payment_hash, "status": "connected", "timestamp": datetime.now().isoformat()}
            )
            yield f"data: {message}\n\n"

            while True:
                if await request.is_disconnected():
                    logging.info(f"Client disconnected from payment_hash={payment_hash}")
                    break

                try:
                    msg = await q.get()
                    yield f"data: {msg}\n\n"
                except Exception as e:
                    logging.error(f"Error sending SSE message: {e}")
                    break

        except Exception as e:
            logging.error(f"Error in event stream: {e}")
        finally:
            # Clean up when client disconnects
            if payment_hash in connections:
                connections[payment_hash] = [conn for conn in connections[payment_hash] if conn.queue != q]
                if not connections[payment_hash]:
                    del connections[payment_hash]
                logging.info(f"Cleaned up connection for payment_hash={payment_hash}")

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream;charset=utf-8",
        },
    )


def notify_clients_of_payment_status(
    payment_hash: str,
    status: str = "paid",
    message: Optional[str] = "Payment received successfully",
    tweet_url: Optional[str] = None,
):
    """Send payment status update to all connected clients"""
    if payment_hash not in connections:
        return
    
    payload = {
        "payment_hash": payment_hash,
        "status": status,
        "message": message,
        "timestamp": datetime.now().isoformat(),
    }

    if tweet_url:
        payload["tweet_url"] = tweet_url

    # Create the message only once
    update = json.dumps(payload)

    dead_connections = []
    for conn in connections[payment_hash]:
        try:
            conn.queue.put_nowait(update)
        except Exception as e:
            logging.error(f"Failed to send message to client: {e}")
            dead_connections.append(conn)

    # Clean up any dead connections
    if dead_connections:
        connections[payment_hash] = [conn for conn in connections[payment_hash] if conn not in dead_connections]
        if not connections[payment_hash]:
            del connections[payment_hash]


async def cleanup_stale_connections():
    """Remove connections that are older than 30 minutes"""
    while True:
        try:
            now = datetime.now()
            timeout = timedelta(minutes=30)

            for payment_hash in list(connections.keys()):
                # Remove old connections
                stale_connections = [conn for conn in connections[payment_hash] if (now - conn.connected_at) > timeout]

                if stale_connections:
                    connections[payment_hash] = [
                        conn for conn in connections[payment_hash] if conn not in stale_connections
                    ]
                    logging.info(f"Removed {len(stale_connections)} stale connections for {payment_hash}")

                # Remove empty payment_hash entries
                if not connections[payment_hash]:
                    del connections[payment_hash]
                    logging.info(f"Removed empty payment_hash entry: {payment_hash}")

            await sleep(300)  # Run cleanup every 5 minutes
        except Exception as e:
            logging.error(f"Error in cleanup_stale_connections: {e}")
            await sleep(60)  # Wait a minute before retrying if there's an error
