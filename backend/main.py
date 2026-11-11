from __future__ import annotations

import json
from datetime import UTC, datetime

import cv2
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from domain_models import SessionDocument


app = FastAPI(title="Casual Cards Local Service", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict[str, object]:
    return {
        "status": "ok",
        "service": "casual-cards-local",
        "opencvVersion": cv2.__version__,
        "arucoAvailable": hasattr(cv2, "aruco"),
        "timestamp": datetime.now(UTC).isoformat(),
    }


@app.get("/api/domain-schema")
async def domain_schema() -> dict[str, object]:
    return SessionDocument.model_json_schema()


@app.websocket("/ws/card-poses")
async def card_poses(websocket: WebSocket) -> None:
    await websocket.accept()
    await websocket.send_json(
        {
            "type": "service.ready",
            "inputSource": "camera",
            "poses": [],
        }
    )
    try:
        while True:
            message = await websocket.receive_text()
            if message == "ping":
                await websocket.send_text("pong")
                continue
            await websocket.send_text(
                json.dumps({"type": "service.echo", "message": message})
            )
    except WebSocketDisconnect:
        return


def main() -> None:
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    main()
