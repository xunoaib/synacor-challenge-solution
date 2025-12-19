import sys
from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import pairwise, product

GRID_LIST = [
    ['*', 8, '-', 1],
    [4, '*', 11, '*'],
    ['+', 4, '-', 18],
    [22, '-', 9, '*'],
]

GRID = {(r, c): GRID_LIST[r][c] for r, c in product(range(4), range(4))}

DIR_TO_CMD = {
    (-1, 0): 'n',
    (1, 0): 's',
    (0, 1): 'e',
    (0, -1): 'w',
}


@dataclass(frozen=True, order=True)
class State:
    pos: tuple[int, int]
    value: int = 0
    op: str | None = '+'


def move_state(state: State, newpos: tuple[int, int]):
    '''Moves a given state to the new position. Returns a modified copy'''
    gridch = GRID[newpos]

    if isinstance(gridch, int):
        newop = None
        match state.op:
            case '+':
                newvalue = state.value + gridch
            case '-':
                newvalue = state.value - gridch
            case '*':
                newvalue = state.value * gridch
            case _:
                print("ya dun goof'd:", repr(newop))
                newvalue = state.value
    else:
        newop = gridch
        newvalue = state.value

    return State(newpos, newvalue, newop)


def neighbors(r, c):
    for roff in (-1, 0, 1):
        for coff in (-1, 0, 1):
            newpos = r + roff, c + coff
            if (roff, coff) != (0, 0) and 0 in (roff, coff) and newpos in GRID:
                yield newpos


def next_states(state):
    states = []
    for newpos in neighbors(*state.pos):
        newstate = move_state(state, newpos)
        states.append(newstate)
    return states


def main():
    goal_val = 30  # target value to reach
    goal_pos = (0, 3)  # end at the upper right corner
    start_pos = (3, 0)  # start at the lower left corner
    state = State(start_pos, GRID[start_pos])

    q = [(0, state)]
    visited = {}
    iterations = 0

    while q:
        iterations += 1
        moves, state = heappop(q)

        if state.value == goal_val and state.pos == goal_pos:
            break

        for next_state in next_states(state):
            # avoid revisiting starting position
            if next_state.pos == start_pos:
                continue

            # avoid visiting goal unless puzzle is solved
            if next_state.pos == goal_pos and next_state.value != goal_val:
                continue

            if next_state not in visited:
                visited[next_state] = state
                heappush(q, (moves + 1, next_state))

    # reconstruct solution
    solution = [state]
    while state := visited.get(state):
        solution.append(state)

    # convert solution to NESW directions
    directions = []
    for s1, s2 in pairwise(solution[::-1]):
        roff, coff = [a - b for a, b in zip(s2.pos, s1.pos)]
        command = DIR_TO_CMD[(roff, coff)]
        directions.append(command)

    print(
        f'found {len(directions)} move solution after {iterations} iterations',
        file=sys.stderr
    )
    macro = ';'.join(directions)
    print(macro)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
