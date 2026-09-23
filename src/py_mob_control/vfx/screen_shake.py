"""Trauma-based dynamic 2D screen shake system."""

import random
from typing import Tuple


class ScreenShake:
    """Non-linear trauma screen shake with exponential decay."""

    def __init__(self, max_offset: float = 18.0, decay_rate: float = 2.4) -> None:
        self.trauma: float = 0.0
        self.max_offset: float = max_offset
        self.decay_rate: float = decay_rate

    def add_trauma(self, amount: float) -> None:
        """Add trauma clamped to 1.0."""
        self.trauma = min(1.0, self.trauma + amount)

    def update(self, dt: float) -> None:
        """Decay trauma over time."""
        if self.trauma > 0.0:
            self.trauma = max(0.0, self.trauma - (self.decay_rate * dt))

    def get_offset(self) -> Tuple[float, float]:
        """Compute pixel offset using non-linear trauma squared."""
        if self.trauma <= 0.001:
            return (0.0, 0.0)

        shake = self.trauma * self.trauma
        ox = (random.random() * 2.0 - 1.0) * self.max_offset * shake
        oy = (random.random() * 2.0 - 1.0) * self.max_offset * shake
        return (ox, oy)
