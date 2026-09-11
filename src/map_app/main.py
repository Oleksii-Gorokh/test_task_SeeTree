from __future__ import annotations

import os
from pathlib import Path
from uuid import UUID

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .failure import RandomFailurePolicy
from .models import Marker, MarkerCreate, MarkerUpdate
from .repository import MarkerRepository


BASE_DIR = Path(__file__).resolve().parents[2]
STATIC_DIR = BASE_DIR / "frontend"


def create_app(
    repository: MarkerRepository | None = None,
    failure_policy: RandomFailurePolicy | None = None,
) -> FastAPI:
    app = FastAPI(title="Map Marker Editor API", version="0.1.0")
    app.state.repository = repository or MarkerRepository()
    app.state.failure_policy = failure_policy or RandomFailurePolicy(
        float(os.getenv("MARKER_FAILURE_RATE", "0.2"))
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/markers", response_model=list[Marker])
    def list_markers(request: Request) -> list[Marker]:
        return request.app.state.repository.list()

    @app.post("/api/markers", response_model=Marker, status_code=status.HTTP_201_CREATED)
    def create_marker(payload: MarkerCreate, request: Request) -> Marker:
        if request.app.state.failure_policy.should_fail():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Marker service is temporarily unavailable. Please try again.",
            )
        return request.app.state.repository.create(payload)

    @app.patch("/api/markers/{marker_id}", response_model=Marker)
    def update_marker(marker_id: UUID, payload: MarkerUpdate, request: Request) -> Marker:
        marker = request.app.state.repository.update(marker_id, payload)
        if marker is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Marker not found")
        return marker

    @app.delete("/api/markers/{marker_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
    def delete_marker(marker_id: UUID, request: Request) -> None:
        if not request.app.state.repository.delete(marker_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Marker not found")

    if STATIC_DIR.exists():
        app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

        @app.get("/", include_in_schema=False)
        def serve_index() -> FileResponse:
            return FileResponse(STATIC_DIR / "index.html")

    return app


app = create_app()
