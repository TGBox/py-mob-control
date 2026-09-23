"""Spatial Hash Grid for high-performance 2D entity collision and separation.

Allows O(1) average lookup for nearby mobs, enabling 1,000+ units to run smoothly at 60 FPS.
"""

from typing import Dict, List, Set, Tuple, Any
import math


class SpatialGrid:
    """2D spatial partitioning grid with integer cell hashing."""

    def __init__(self, cell_size: float = 35.0) -> None:
        self.cell_size: float = cell_size
        self.cells: Dict[Tuple[int, int], List[Any]] = {}

    def clear(self) -> None:
        """Clear all registered entities from grid."""
        self.cells.clear()

    def _hash(self, x: float, y: float) -> Tuple[int, int]:
        """Convert float world coordinates to grid cell index."""
        return int(math.floor(x / self.cell_size)), int(math.floor(y / self.cell_size))

    def insert(self, entity: Any) -> None:
        """Insert an entity with .x, .y into the spatial grid."""
        cell = self._hash(entity.x, entity.y)
        if cell not in self.cells:
            self.cells[cell] = []
        self.cells[cell].append(entity)

    def populate(self, entities: List[Any]) -> None:
        """Populate the grid with a list of entities."""
        self.clear()
        for e in entities:
            if getattr(e, "alive", True):
                self.insert(e)

    def query_radius(self, x: float, y: float, radius: float) -> List[Any]:
        """Find all entities within a given radius of (x, y)."""
        min_cell = self._hash(x - radius, y - radius)
        max_cell = self._hash(x + radius, y + radius)
        r_sq = radius * radius
        results: List[Any] = []

        for cx in range(min_cell[0], max_cell[0] + 1):
            for cy in range(min_cell[1], max_cell[1] + 1):
                cell_entities = self.cells.get((cx, cy))
                if not cell_entities:
                    continue
                for e in cell_entities:
                    dx = e.x - x
                    dy = e.y - y
                    if dx * dx + dy * dy <= r_sq:
                        results.append(e)
        return results

    def solve_separation(self, mobs: List[Any], dt: float, push_strength: float = 180.0) -> None:
        """Apply soft repulsion force between nearby mobs so they flow like a liquid crowd."""
        for mob in mobs:
            if not getattr(mob, "alive", True):
                continue
            cx, cy = self._hash(mob.x, mob.y)
            # Check 3x3 surrounding cells
            for ox in (-1, 0, 1):
                for oy in (-1, 0, 1):
                    cell = (cx + ox, cy + oy)
                    neighbors = self.cells.get(cell)
                    if not neighbors:
                        continue
                    for other in neighbors:
                        if other is mob or not getattr(other, "alive", True):
                            continue
                        dx = mob.x - other.x
                        dy = mob.y - other.y
                        dist_sq = dx * dx + dy * dy
                        min_dist = mob.radius + other.radius
                        if 0.001 < dist_sq < min_dist * min_dist:
                            dist = math.sqrt(dist_sq)
                            overlap = (min_dist - dist) / min_dist
                            # Normalized repulsion
                            nx = dx / dist
                            ny = dy / dist
                            force = overlap * push_strength * dt
                            # Champion has higher inertia
                            mob_mass = 4.0 if getattr(mob, "is_champion", False) else 1.0
                            other_mass = 4.0 if getattr(other, "is_champion", False) else 1.0
                            ratio = other_mass / (mob_mass + other_mass)

                            mob.x += nx * force * ratio
                            mob.y += ny * force * ratio * 0.4  # dampen Y push so forward stream continues
