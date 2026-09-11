from __future__ import annotations

from threading import RLock
from uuid import UUID

from .models import Marker, MarkerCreate, MarkerUpdate


class MarkerRepository:
    """Thread-safe in-memory storage for markers."""

    def __init__(self) -> None:
        self._markers: dict[UUID, Marker] = {}
        self._lock = RLock()

    def list(self) -> list[Marker]:
        with self._lock:
            return list(self._markers.values())

    def create(self, payload: MarkerCreate) -> Marker:
        marker = Marker(**payload.model_dump())
        with self._lock:
            self._markers[marker.id] = marker
        return marker

    def update(self, marker_id: UUID, payload: MarkerUpdate) -> Marker | None:
        with self._lock:
            current = self._markers.get(marker_id)
            if current is None:
                return None
            changes = payload.model_dump(exclude_unset=True)
            values = current.model_dump()
            values.update(changes)
            updated = Marker.model_validate(values)
            self._markers[marker_id] = updated
            return updated

    def delete(self, marker_id: UUID) -> bool:
        with self._lock:
            return self._markers.pop(marker_id, None) is not None

    def clear(self) -> None:
        with self._lock:
            self._markers.clear()
