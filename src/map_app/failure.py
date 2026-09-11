from __future__ import annotations

import random
from collections.abc import Callable


class RandomFailurePolicy:
    """Fail a request randomly to model an unreliable persistence service."""

    def __init__(self, failure_rate: float = 0.2, random_fn: Callable[[], float] | None = None) -> None:
        if not 0 <= failure_rate <= 1:
            raise ValueError("failure_rate must be between 0 and 1")
        self.failure_rate = failure_rate
        self._random = random_fn or random.random

    def should_fail(self) -> bool:
        return self._random() < self.failure_rate
