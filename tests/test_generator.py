from __future__ import annotations

from collections import deque

import pytest

from maze_pdf.generator import Maze, generate, generate_prim, generate_with, solve


def _count_passages(maze: Maze) -> int:
    passages = 0
    for y in range(maze.height):
        for x in range(maze.width):
            cell = maze.cells[y][x]
            if not cell.east and x + 1 < maze.width:
                passages += 1
            if not cell.south and y + 1 < maze.height:
                passages += 1
    return passages


def _is_connected(maze: Maze) -> bool:
    visited = [[False] * maze.width for _ in range(maze.height)]
    q: deque[tuple[int, int]] = deque([(0, 0)])
    visited[0][0] = True
    count = 1
    while q:
        x, y = q.popleft()
        cell = maze.cells[y][x]
        for dx, dy, wall in (
            (0, -1, "north"),
            (0, 1, "south"),
            (1, 0, "east"),
            (-1, 0, "west"),
        ):
            if 0 <= x + dx < maze.width and 0 <= y + dy < maze.height:
                if not getattr(cell, wall):
                    if not visited[y + dy][x + dx]:
                        visited[y + dy][x + dx] = True
                        count += 1
                        q.append((x + dx, y + dy))
    return count == maze.width * maze.height


@pytest.mark.parametrize("n", [2, 5, 15, 25, 40])
def test_perfect_maze_properties(n: int) -> None:
    maze = generate(n, n, seed=123)
    assert _count_passages(maze) == n * n - 1
    assert _is_connected(maze)


def test_same_seed_produces_identical_maze() -> None:
    a = generate(20, 20, seed=42)
    b = generate(20, 20, seed=42)
    for y in range(a.height):
        for x in range(a.width):
            ca, cb = a.cells[y][x], b.cells[y][x]
            assert (ca.north, ca.south, ca.east, ca.west) == (
                cb.north,
                cb.south,
                cb.east,
                cb.west,
            )


def test_different_seeds_produce_different_mazes() -> None:
    a = generate(20, 20, seed=1)
    b = generate(20, 20, seed=2)
    diffs = 0
    for y in range(a.height):
        for x in range(a.width):
            ca, cb = a.cells[y][x], b.cells[y][x]
            if (ca.north, ca.south, ca.east, ca.west) != (
                cb.north,
                cb.south,
                cb.east,
                cb.west,
            ):
                diffs += 1
    assert diffs > 0


def test_entry_and_exit_open() -> None:
    maze = generate(10, 10, seed=7)
    assert maze.entry == (0, 0)
    assert maze.exit == (9, 9)
    assert maze.cells[0][0].north is False
    assert maze.cells[9][9].south is False


def test_invalid_width_raises() -> None:
    with pytest.raises(ValueError, match="width"):
        generate(1, 10)


def test_invalid_height_raises() -> None:
    with pytest.raises(ValueError, match="height"):
        generate(10, 0)


def test_rectangular_maze() -> None:
    maze = generate(8, 12, seed=1)
    assert maze.width == 8
    assert maze.height == 12
    assert _count_passages(maze) == 8 * 12 - 1
    assert _is_connected(maze)


@pytest.mark.parametrize("n", [3, 10, 25])
def test_prim_perfect_maze_properties(n: int) -> None:
    maze = generate_prim(n, n, seed=1)
    assert _count_passages(maze) == n * n - 1
    assert _is_connected(maze)


def test_prim_deterministic_with_seed() -> None:
    a = generate_prim(15, 15, seed=42)
    b = generate_prim(15, 15, seed=42)
    for y in range(a.height):
        for x in range(a.width):
            ca, cb = a.cells[y][x], b.cells[y][x]
            assert (ca.north, ca.south, ca.east, ca.west) == (
                cb.north, cb.south, cb.east, cb.west,
            )


def test_dfs_and_prim_produce_different_mazes() -> None:
    # Misma grilla + mismo seed, distinto algoritmo → mazes distintos.
    a = generate(20, 20, seed=7)
    b = generate_prim(20, 20, seed=7)
    diffs = 0
    for y in range(a.height):
        for x in range(a.width):
            ca, cb = a.cells[y][x], b.cells[y][x]
            if (ca.north, ca.south, ca.east, ca.west) != (
                cb.north, cb.south, cb.east, cb.west,
            ):
                diffs += 1
    assert diffs > 0


def test_generate_with_dispatch() -> None:
    m1 = generate_with("dfs", 10, 10, seed=1)
    m2 = generate(10, 10, seed=1)
    for y in range(m1.height):
        for x in range(m1.width):
            assert vars(m1.cells[y][x]) == vars(m2.cells[y][x])


def test_generate_with_unknown_algorithm_raises() -> None:
    with pytest.raises(ValueError, match="algoritmo"):
        generate_with("astar", 10, 10, seed=1)


def test_solve_returns_path_from_entry_to_exit() -> None:
    maze = generate(10, 10, seed=1)
    path = solve(maze)
    assert path[0] == maze.entry
    assert path[-1] == maze.exit
    # Cada paso consecutivo es un vecino adyacente.
    for (x1, y1), (x2, y2) in zip(path, path[1:]):
        assert abs(x1 - x2) + abs(y1 - y2) == 1


def test_solve_path_uses_only_passages() -> None:
    maze = generate(8, 8, seed=5)
    path = solve(maze)
    for (x1, y1), (x2, y2) in zip(path, path[1:]):
        cell = maze.cells[y1][x1]
        if x2 == x1 + 1:
            assert not cell.east
        elif x2 == x1 - 1:
            assert not cell.west
        elif y2 == y1 + 1:
            assert not cell.south
        elif y2 == y1 - 1:
            assert not cell.north


def test_solve_unique_path_length() -> None:
    # En un maze perfecto el camino es único. Longitud = al menos la distancia de Manhattan.
    n = 15
    maze = generate(n, n, seed=3)
    path = solve(maze)
    assert len(path) >= 2 * n - 1  # mínimo posible en un maze perfecto NxN
