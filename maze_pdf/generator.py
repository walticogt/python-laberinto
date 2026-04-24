from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field


@dataclass
class Cell:
    north: bool = True
    south: bool = True
    east: bool = True
    west: bool = True


@dataclass
class Maze:
    width: int
    height: int
    cells: list[list[Cell]]
    entry: tuple[int, int] = (0, 0)
    exit: tuple[int, int] = field(default=(0, 0))


_DIRS = (
    ("north", 0, -1, "south"),
    ("south", 0, 1, "north"),
    ("east", 1, 0, "west"),
    ("west", -1, 0, "east"),
)

ALGORITHMS = ("dfs", "prim")


def generate(width: int, height: int, seed: int | None = None) -> Maze:
    if width < 2:
        raise ValueError(f"width debe ser >= 2, se recibió {width}")
    if height < 2:
        raise ValueError(f"height debe ser >= 2, se recibió {height}")

    rng: random.Random = random.Random(seed) if seed is not None else random.SystemRandom()

    cells = [[Cell() for _ in range(width)] for _ in range(height)]
    visited = [[False] * width for _ in range(height)]

    stack: list[tuple[int, int]] = [(0, 0)]
    visited[0][0] = True

    while stack:
        x, y = stack[-1]
        neighbours = []
        for name, dx, dy, opposite in _DIRS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height and not visited[ny][nx]:
                neighbours.append((name, nx, ny, opposite))

        if not neighbours:
            stack.pop()
            continue

        name, nx, ny, opposite = rng.choice(neighbours)
        setattr(cells[y][x], name, False)
        setattr(cells[ny][nx], opposite, False)
        visited[ny][nx] = True
        stack.append((nx, ny))

    cells[0][0].north = False
    cells[height - 1][width - 1].south = False

    return Maze(
        width=width,
        height=height,
        cells=cells,
        entry=(0, 0),
        exit=(width - 1, height - 1),
    )


def generate_prim(width: int, height: int, seed: int | None = None) -> Maze:
    """Randomized Prim's algorithm — produces perfect mazes with shorter corridors
    and more branching than DFS. Same public contract as `generate`.
    """
    if width < 2:
        raise ValueError(f"width debe ser >= 2, se recibió {width}")
    if height < 2:
        raise ValueError(f"height debe ser >= 2, se recibió {height}")

    rng: random.Random = random.Random(seed) if seed is not None else random.SystemRandom()

    cells = [[Cell() for _ in range(width)] for _ in range(height)]
    visited = [[False] * width for _ in range(height)]

    # Start at (0,0); frontier = edges from visited to unvisited.
    visited[0][0] = True
    frontier: list[tuple[int, int, int, int, str, str]] = []

    def _add_edges(fx: int, fy: int) -> None:
        for name, dx, dy, opposite in _DIRS:
            nx, ny = fx + dx, fy + dy
            if 0 <= nx < width and 0 <= ny < height and not visited[ny][nx]:
                frontier.append((fx, fy, nx, ny, name, opposite))

    _add_edges(0, 0)

    while frontier:
        i = rng.randrange(len(frontier))
        fx, fy, tx, ty, name, opposite = frontier[i]
        # Swap-pop for O(1) removal.
        frontier[i] = frontier[-1]
        frontier.pop()

        if visited[ty][tx]:
            continue

        setattr(cells[fy][fx], name, False)
        setattr(cells[ty][tx], opposite, False)
        visited[ty][tx] = True
        _add_edges(tx, ty)

    cells[0][0].north = False
    cells[height - 1][width - 1].south = False

    return Maze(
        width=width,
        height=height,
        cells=cells,
        entry=(0, 0),
        exit=(width - 1, height - 1),
    )


def generate_with(
    algorithm: str,
    width: int,
    height: int,
    seed: int | None = None,
) -> Maze:
    """Dispatch to `generate` (DFS) or `generate_prim` by algorithm name."""
    if algorithm == "dfs":
        return generate(width, height, seed)
    if algorithm == "prim":
        return generate_prim(width, height, seed)
    raise ValueError(
        f"algoritmo desconocido: {algorithm!r}. Opciones: {', '.join(ALGORITHMS)}"
    )


def solve(maze: Maze) -> list[tuple[int, int]]:
    """Return the unique cell-by-cell path from maze.entry to maze.exit.

    Since the maze is perfect (single path between any two cells), BFS finds it
    in O(width * height). The returned list is ordered from entry to exit,
    inclusive of both endpoints.
    """
    start = maze.entry
    end = maze.exit
    parents: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    q: deque[tuple[int, int]] = deque([start])

    _wall_dirs = (
        ("north", 0, -1),
        ("south", 0, 1),
        ("east", 1, 0),
        ("west", -1, 0),
    )

    while q:
        x, y = q.popleft()
        if (x, y) == end:
            break
        cell = maze.cells[y][x]
        for wall, dx, dy in _wall_dirs:
            if getattr(cell, wall):
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < maze.width and 0 <= ny < maze.height and (nx, ny) not in parents:
                parents[(nx, ny)] = (x, y)
                q.append((nx, ny))

    if end not in parents:
        raise ValueError("maze exit is unreachable from entry — maze is not connected")

    path: list[tuple[int, int]] = []
    cur: tuple[int, int] | None = end
    while cur is not None:
        path.append(cur)
        cur = parents[cur]
    path.reverse()
    return path
