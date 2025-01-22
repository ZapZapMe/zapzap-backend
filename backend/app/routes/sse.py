from typing import Dict, List

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/sse", tags=["sse"])

# In-memory map: payment_hash => list of event queues
connections: Dict[str, List] = {}


@router.get("/subscribe")
async def subscribe_to_payment(request: Request, payment_hash: str):
    # Create a queue for this client so we can push SSE events to it
    from asyncio import Queue

    q = Queue()
    if payment_hash not in connections:
        connections[payment_hash] = []
    connections[payment_hash].append(q)

    # Stream response: yield SSE from the queue
    async def event_stream():
        try:
            while True:
                if await request.is_disconnected():
                    break
                msg = await q.get()
                yield f"data: {msg}\n\n"
        except Exception:
            pass
        finally:
            # remove the queue when disconnected
            connections[payment_hash].remove(q)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
