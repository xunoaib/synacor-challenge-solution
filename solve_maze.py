import argparse
import re
import string
import sys

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
    vm = vm.clone()
    vm.read()
    vm.send('look')
    data = vm.read()

    if m := re.search(
        r'\nThings of interest here:\n(.*?)\n\n', data, re.DOTALL
    ):
        return re.findall(r'- (.*?)\n', m.group(1) + '\n')

    return []


def find_exits(vm: EnhancedCPU):
    vm = vm.clone()
    vm.read()
    vm.send('look')
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


def explore(current: EnhancedCPU):
    '''Explore all possible paths from the given CPU state. Cycles are skipped'''

    current.read()
    current.send('look')  # NOTE: won't show previous output

    vms: dict[int, EnhancedCPU] = {}
    # map current vm location => [(north_room_id, 'north'), ...]
    edges: dict[int, list[tuple[int, str]]] = {}
    descriptions = {current.location: current.read().strip()}

    q = [current]

    while q:
        current = q.pop(0)
        states = list(neighbor_locs(current))
        edges[current.location] = [(n.location, move) for move, n in states]
        for _, n in states:
            if n.location not in vms:
                descriptions[n.location] = n.read().strip()
                vms[n.location] = n
                q.append(n)

    return edges, descriptions, vms


def bruteforce_location_addrs(vm: EnhancedCPU):

    known_locs = [
        2317, 2322, 2327, 2332, 2337, 2342, 2347, 2352, 2357, 2362, 2367, 2372,
        2377, 2382, 2387, 2392, 2397, 2402, 2407, 2417, 2422, 2427, 2432, 2437,
        2442, 2447, 2452, 2457, 2463, 2468, 2473, 2478, 2483, 2488, 2493, 2648,
        2653, 2658, 2663
    ]

    new_locs = {}

    vm.read()
    for loc in range(2300, 3000):
        if loc in known_locs:
            continue

        v = vm.clone()
        v.location = loc
        try:
            text = v.sendcopy('look').read()
            l = v.location
            if l not in known_locs and all(
                c in string.printable for c in text
            ):
                print('Adding', l)
                new_locs[l] = text
        except (KeyError, IndexError):
            pass

    for l, text in sorted(new_locs.items()):
        print(l, repr(text))
        print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', default='challenge.bin')
    args = parser.parse_args()

    print('Loading binary:', args.file)

    vm = EnhancedCPU(args.file)
    vm.run()

    if '-b' in sys.argv:
        bruteforce_location_addrs(vm)
        exit()

    def print_new_locs(known_locs, vms):
        for loc in set(vms) - set(known_locs):
            v = vms[loc]
            v.read()
            d = v.sendcopy('look').read()
            if m := re.search(r'== (.*?) ==', d):
                d = m.group(1)
            print(f'New location: {loc} ({d})')

    def find_all_states(vm):
        _, descs, vms = explore(vm)
        item_addrs = identify_item_addrs(list(vms.values()))
        print(f'Found {len(vms)} states and {len(item_addrs)} items\n')
        return descs, vms, item_addrs

    def take_all_items(vm, item_addrs):
        vm = vm.clone()
        print()
        for name, addr in item_addrs.items():
            print(f'Giving mem[{addr}] = {name}')
            vm.memory[addr] = 0
        print()
        return vm

    def find_and_collect_all(vm, known_locs):
        descs, vms, item_addrs = find_all_states(vm)
        print_new_locs(known_locs, vms)
        vm = take_all_items(vm, item_addrs)
        return vm, descs, known_locs | vms

    vm, descs, known_locs = find_and_collect_all(vm, {})

    print('>> Using can and lantern')
    vm.send('use can')
    vm.send('use lantern')

    vm, descs, known_locs = find_and_collect_all(vm, known_locs)

    code4 = next(
        m.group(1) for d in descs.values()
        if (m := re.search('Chiseled on the wall.*\n\n    (.*?)\n', d))
    )
    print(f'\033[92mCode #4: {code4}\033[0m')

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

    vm, descs, known_locs = find_and_collect_all(vm, known_locs)

    print('>> Using teleporter')
    vm.send('use teleporter')

    vm, descs, known_locs = find_and_collect_all(vm, known_locs)

    print('>> Using teleporter again')
    vm.teleport_call_addr = utils.find_teleporter_call(vm.memory)
    vm.registers[7] = 25734
    vm.send('use teleporter')

    vm, descs, known_locs = find_and_collect_all(vm, known_locs)

    # Go to antechamber
    vm.location = next(
        loc for loc, desc in descs.items() if '== Vault Antechamber ==' in desc
    )

    # Solver antechamber
    vm.send('look')
    vm.send('take orb')
    vm.send('n;e;e;n;w;s;e;e;w;n;n;e')
    vm.send('vault')
    vm.send('take mirror')
    vm.read()
    vm.send('use mirror')

    resp = vm.read()
    if m := re.search(
        'Through the mirror, you see "(.*)" scrawled in charcoal', resp
    ):
        print('\033[92mCode #8: ' + m.group(1) + '\033[0m')
    else:
        print('\033[91mError! Last code not found\033[0m')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
