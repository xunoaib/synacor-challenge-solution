#!/usr/bin/env python3
import json
import pickle
import re
from heapq import heappop, heappush

import utils
from enhancedcpu import EnhancedCPU


def neighbor_locs(vm: EnhancedCPU) -> list[tuple[str, EnhancedCPU]]:
    exits = find_exits(vm)
    vms = []
    for direction in exits:
        n = vm.sendcopy(direction)
        vms.append((direction, n))
    return vms


def neighbor_items(vm: EnhancedCPU):
    items = find_items(vm)
    vms = []
    for item in items:
        cmd = 'take ' + item
        n = vm.sendcopy(cmd)
        vms.append((cmd, n))
    return vms


def all_neighbors(vm: EnhancedCPU):
    return neighbor_items(vm) + neighbor_locs(vm)


def find_items(vm: EnhancedCPU):
    vm.read()
    vm = vm.sendcopy('look')
    data = vm.read()

    if m := re.search(
        r'\nThings of interest here:\n(.*?)\n\n', data, re.DOTALL
    ):
        return re.findall(r'- (.*?)\n', m.group(1) + '\n')

    return []


def find_exits(vm: EnhancedCPU):
    vm.read()
    vm = vm.sendcopy('look')
    data = vm.read()

    if m := re.search(
        r'\nThere (is|are) (\d+) exits?:\n(.*)\nWhat do you do?', data,
        re.DOTALL
    ):
        return re.findall(r'- (.*?)\n', m.group(3))
    return []


def explore(current: EnhancedCPU, verbose=True):
    '''Explore all possible paths from the given CPU state. Cycles are skipped'''

    current.read()
    current.send('look')

    vms: dict[int, EnhancedCPU] = {}
    # map current vm location => [(north_room_id, 'north'), ...]
    edges: dict[int, list[tuple[int, str]]] = {}
    descriptions = {current.location: current.read().strip()}

    q = [current]

    while q:
        current = q.pop(0)
        if verbose:
            print(
                f'\033[92m{current.location}',
                descriptions[current.location].split('\n')[0], '\033[0m'
            )
            print(descriptions[current.location])

        states = list(neighbor_locs(current))
        edges[current.location] = [
            (neighbor.location, next_move) for next_move, neighbor in states
        ]
        for _, neighbor in states:
            if neighbor.location not in vms:
                neighbor.read()
                neighbor.send('look')
                descriptions[neighbor.location] = neighbor.read().strip()
                vms[neighbor.location] = neighbor
                q.append(neighbor)

    return edges, descriptions, vms


# def find_path(edges: dict, src_vm: EnhancedCPU, tar_loc):
#     q = [(0, src_vm.location)]
#
#     while q:
#         cost, loc = heappop(q)


def main():
    # vm = EnhancedCPU('challenge.bin')
    vm = EnhancedCPU.from_snapshot_file('snapshots/start')
    # vm.send('.giveall')
    # vm = EnhancedCPU.from_snapshot_file('snapshots/ladder')
    # vm = EnhancedCPU.from_snapshot_file('snapshots/beach')

    # Find all states (without picking up items)
    edges, descs, vms = explore(vm, verbose=False)

    # Find states with items
    item_addrs = []
    for loc, vm in vms.items():
        if items := find_items(vm):
            for item in items:
                vm2 = vm.sendcopy('take ' + item)
                result = utils.diff_vms(vm, vm2)
                # print(f'took {item} => {result}')
                addr = next(
                    idx for idx, old, new in result.get('memory', [])
                    if old and not new
                )
                print(f'took {item} => {addr}')

    return

    # # discover all rooms (and cache to file)
    # vm = EnhancedCPU.from_snapshot_file('snapshots/beach')
    # vm.run()
    # edges, descs, vms = explore(vm)

    # with open('graph.pickle', 'wb') as f:
    #     f.write(pickle.dumps(ret))

    # # # load cached results generated above
    # with open('graph.pickle','rb') as f:
    #     ret = edges, descs, vms = pickle.loads(f.read())

    # print()
    # __import__('pprint').pprint(edges)

    for loc, desc in descs.items():
        # if 'Vault Door' in desc:
        #     print(loc)
        #     vms[loc].send('.save vault')

        # if 'journal' in desc:
        #     print(desc)
        #     vms[loc].interactive()
        print()
        print(desc)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
