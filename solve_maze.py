#!/usr/bin/env python3
import re

from debugger import Debugger

def next_states(vm: Debugger):
    exits = get_exits(vm)
    vms = []
    for direction in exits:
        n = vm.sendcopy(direction)
        vms.append((direction, n))
    return vms

def get_exits(vm: Debugger):
    vm = vm.sendcopy('look')
    data = vm.read()
    if exitsstr := re.search(r'\nThere (is|are) (\d+) exits?:\n(.*)\nWhat do you do?', data, re.DOTALL):
        return re.findall(r'- (.*?)\n', exitsstr.group(3))
    return []

def main():
    vm = Debugger.from_snapshot_file('snapshots/ladder')
    vm.debug_cmd('giveall')
    vm.send('look')

    visited = {vm.location: vm}
    q = [(vm, tuple())]

    while q:
        current, moves = q.pop(0)
        print()
        print(current, moves)
        print()
        print(current.read().strip())

        states = next_states(current)
        for next_move, neighbor in states:
            if next_move == 'ladder':
                continue  # avoid leaving the maze
            if neighbor.location not in visited:
                visited[neighbor.location] = neighbor
                q.append((neighbor, moves + (next_move,)))

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
