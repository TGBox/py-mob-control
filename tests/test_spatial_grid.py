"""Unit tests for SpatialGrid spatial partitioning and collision queries."""

import pytest
from py_mob_control.game.entities.mob import Mob, Team
from py_mob_control.engine.spatial_grid import SpatialGrid


def test_spatial_grid_insertion_and_query():
    grid = SpatialGrid(cell_size=30.0)
    mob1 = Mob(x=100.0, y=100.0, team=Team.PLAYER)
    mob2 = Mob(x=110.0, y=105.0, team=Team.ENEMY)
    mob3 = Mob(x=400.0, y=400.0, team=Team.PLAYER)

    grid.populate([mob1, mob2, mob3])

    # Query near (100, 100) with radius 20
    neighbors = grid.query_radius(100.0, 100.0, radius=20.0)
    assert mob1 in neighbors
    assert mob2 in neighbors
    assert mob3 not in neighbors


def test_spatial_grid_separation():
    grid = SpatialGrid(cell_size=30.0)
    # Two overlapping mobs
    mob1 = Mob(x=100.0, y=100.0, team=Team.PLAYER)
    mob2 = Mob(x=102.0, y=100.0, team=Team.PLAYER)

    initial_dx = abs(mob2.x - mob1.x)
    assert initial_dx == 2.0

    grid.populate([mob1, mob2])
    grid.solve_separation([mob1, mob2], dt=0.05, push_strength=200.0)

    # After separation, distance should have increased
    new_dx = abs(mob2.x - mob1.x)
    assert new_dx > initial_dx
