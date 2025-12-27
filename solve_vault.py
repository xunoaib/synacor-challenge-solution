import sys
from dataclasses import dataclass
from itertools import pairwise

GRID_LIST = [
    ['*', 8, '-', 1],
    [4, '*', 11, '*'],
    ['+', 4, '-', 18],
    [22, '-', 9, '*'],
]

GRID = {
    (r, c): v
    for r, row in enumerate(GRID_LIST)
    for c, v in enumerate(row)
}

DIRS = [(-1, 0), (1, 0), (0, 1), (0, -1)]
DIR_TO_CMD = dict(zip(DIRS, 'nsew'))


@dataclass(frozen=True, order=True)
class State:
    pos: tuple[int, int]
    value: int = 0
    op: str | None = '+'


def move(state: State, newpos: tuple[int, int]):
    v = GRID[newpos]

    if not isinstance(v, int):
        return State(newpos, state.value, v)

    values = {
        '+': state.value + v,
        '-': state.value - v,
        '*': state.value * v,
    }

    assert state.op
    return State(newpos, values[state.op], None)


def neighbors(r, c):
    return {(r + dr, c + dc) for dr, dc in DIRS if (r + dr, c + dc) in GRID}


def next_states(state):
    return [move(state, p) for p in neighbors(*state.pos)]


def solve(
    start_pos: tuple[int, int],
    goal_pos: tuple[int, int],
    goal_val: int,
):
    start_val = GRID[start_pos]
    assert isinstance(start_val, int), f'Invalid starting value: {start_val}'

    state = State(start_pos, start_val)
    q = [state]
    parent = {}
    iterations = 0

    while q:
        iterations += 1
        state = q.pop(0)

        if state.value == goal_val and state.pos == goal_pos:
            break

        for next_state in next_states(state):
            # avoid revisiting starting position
            if next_state.pos == start_pos:
                continue

            # avoid visiting goal unless puzzle is solved
            if next_state.pos == goal_pos and next_state.value != goal_val:
                continue

            if next_state not in parent:
                parent[next_state] = state
                q.append(next_state)

    # reconstruct solution
    solution = [state]
    while state := parent.get(state):
        solution.append(state)

    # convert solution to NESW directions
    directions = []
    for s1, s2 in pairwise(solution[::-1]):
        dr, dc = [a - b for a, b in zip(s2.pos, s1.pos)]
        directions.append(DIR_TO_CMD[dr, dc])

    print(
        f'found {len(directions)} move solution after {iterations} iterations',
        file=sys.stderr
    )
    macro = ';'.join(directions)
    print(macro)

    assert macro == 'n;e;e;n;w;s;e;e;w;n;n;e'


def main():
    goal_val = 30  # target value to reach
    goal_pos = (0, 3)  # end at the upper right corner
    start_pos = (3, 0)  # start at the lower left corner

    solve(start_pos, goal_pos, goal_val)


if __name__ == '__main__':
    main()
