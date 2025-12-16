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


def identify_item_addrs(vms: list[EnhancedCPU]):
    addrs = {}
    for vm in vms:
        if items := find_items(vm):
            for item in items:
                vm2 = vm.sendcopy('take ' + item)
                result = utils.diff_vms(vm, vm2)
                addr = next(
                    idx for idx, old, new in result.get('memory', [])
                    if old and not new
                )
                addrs[item] = addr
    return addrs


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
        edges[current.location] = [(n.location, move) for move, n in states]
        for _, n in states:
            if n.location not in vms:
                n.read()
                n.send('look')
                descriptions[n.location] = n.read().strip()
                vms[n.location] = n
                q.append(n)

    return edges, descriptions, vms


def main():
    # vm = EnhancedCPU('challenge.bin')
    vm = EnhancedCPU.from_snapshot_file('snapshots/start')

    # vm.send('.giveall')
    # vm = EnhancedCPU.from_snapshot_file('snapshots/ladder')
    # vm = EnhancedCPU.from_snapshot_file('snapshots/beach')

    known_locs = {}

    def print_new_locs():
        nonlocal known_locs
        for loc in set(vms) - set(known_locs):
            v = vms[loc]
            v.read()
            d = v.sendcopy('look').read()
            if m := re.search(r'== (.*?) ==', d):
                d = m.group(1)
            print(f'New location: {loc} ({d})')
        known_locs |= vms

    def find_all_states():
        edges, descs, vms = explore(vm, verbose=False)
        item_addrs = identify_item_addrs(list(vms.values()))
        print(f'Found {len(vms)} states and {len(item_addrs)} items')
        # print(item_addrs)
        print()
        return descs, vms, item_addrs

    def take_all_items():
        print()
        for name, addr in item_addrs.items():
            print(f'Giving mem[{addr}] = {name}')
            vm.memory[addr] = 0
        print()

    descs, vms, item_addrs = find_all_states()
    print_new_locs()
    take_all_items()

    print('>> Using can and lantern')
    vm.send('use can')
    vm.send('use lantern')

    descs, vms, item_addrs = find_all_states()
    print_new_locs()
    take_all_items()

    # Go to central hall
    vm.location = next(
        loc for loc, desc in descs.items() if
        'There is a strange monument in the center of the hall with circular slots and unusual'
        in desc
    )

    # Solve coins puzzle
    print('>> Solving coins puzzle')
    vm.send('use blue coin')
    vm.send('use red coin')
    vm.send('use shiny coin')
    vm.send('use concave coin')
    vm.send('use corroded coin')

    descs, vms, item_addrs = find_all_states()
    print_new_locs()
    take_all_items()

    print('>> Using teleporter')
    vm.send('use teleporter')

    descs, vms, item_addrs = find_all_states()
    print_new_locs()
    take_all_items()

    print(vm.flush().sendcopy('look strange book').read())
    vm.interactive()

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
