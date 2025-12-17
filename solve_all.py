import argparse
import hashlib
import re

import utils
from enhancedcpu import EnhancedCPU


def md5(s: str):
    return hashlib.md5(s.encode()).hexdigest()


def reflect(s: str):

    def add(a, b):
        return {a: b, b: a}

    d = add('d', 'b') | add('p', 'q') | add('2', '5')
    return ''.join(d.get(c, c) for c in s)[::-1]


def neighbor_locs(vm: EnhancedCPU) -> list[tuple[str, EnhancedCPU]]:
    exits = find_exits(vm)
    vms = []
    for direction in exits:
        n = vm.sendcopy(direction)
        vms.append((direction, n))
    return vms


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


def find_items(vm: EnhancedCPU):
    vm = vm.clone()
    vm.read()
    vm.send('look')
    data = vm.read()
    m = re.search(r'\nThings of interest here:\n(.*?)\n\n', data, re.DOTALL)
    return re.findall(r'- (.*?)\n', m.group(1) + '\n') if m else []


def identify_item_addrs(vms: list[EnhancedCPU]):
    addrs = {}
    for vm in vms:
        for item in find_items(vm):
            vm2 = vm.sendcopy('take ' + item)
            result = utils.diff_vms(vm, vm2)
            addr = next(
                idx for idx, old, new in result.get('memory', [])
                if old and not new
            )
            addrs[item] = addr
    return addrs


def explore(vm: EnhancedCPU):
    '''Explore all possible paths from the given CPU state. Cycles are skipped'''

    vm.read()
    vm.send('look')  # NOTE: won't show previous output

    vms: dict[int, EnhancedCPU] = {}
    # map current vm location => [(north_room_id, 'north'), ...]
    edges: dict[int, list[tuple[int, str]]] = {}
    descriptions = {vm.location: vm.read().strip()}

    q = [vm]

    while q:
        vm = q.pop(0)
        states = list(neighbor_locs(vm))
        edges[vm.location] = [(n.location, move) for move, n in states]
        for _, n in states:
            if n.location not in vms:
                descriptions[n.location] = n.read().strip()
                vms[n.location] = n
                q.append(n)

    return edges, descriptions, vms


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


def solve_all(arch_spec_fname, challenge_bin_fname):
    print('Loading arch-spec')
    with open(arch_spec_fname) as f:
        data = f.read()

    m1 = re.search("Here's a code for the challenge website: (.*?)\n", data)
    assert m1, 'Missing arch-spec code'
    print(f'\033[92mCode #1: {m1.group(1)}\033[0m: {md5(m1.group(1))}')

    print('Loading binary:', challenge_bin_fname)

    vm = EnhancedCPU(challenge_bin_fname)
    vm.run()
    data = vm.read()

    m2 = re.search('this one into the challenge website: (.*?)\n', data)
    m3 = re.search('The self-test completion code is: (.*?)\n', data)

    assert m2, 'Missing pre-test code'
    assert m3, 'Missing post-test code'

    print(f'\033[92mCode #2: {m2.group(1)}\033[0m: {md5(m2.group(1))}')
    print(f'\033[92mCode #3: {m3.group(1)}\033[0m: {md5(m3.group(1))}')

    vm.send('take tablet')
    vm.read()
    vm.send('use tablet')
    data = vm.read()

    m = re.search(r'You find yourself writing "(.*?)" on the tablet', data)
    assert m, 'Missing code (tablet)'
    print(f'\033[92mCode #4: {m.group(1)}\033[0m: {md5(m.group(1))}')

    vm, descs, known_locs = find_and_collect_all(vm, {})

    print('>> Using can and lantern')
    vm.send('use can')
    vm.send('use lantern')

    vm, descs, known_locs = find_and_collect_all(vm, known_locs)

    code5 = next(
        m.group(1) for d in descs.values()
        if (m := re.search('Chiseled on the wall.*\n\n    (.*?)\n', d))
    )
    print(f'\033[92mCode #5: {code5}\033[0m: {md5(code5)}')

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

    data = vm.read()
    m = re.search(
        r'you think you see a pattern in the stars...\n\s+(.*?)\n', data
    )
    assert m, 'Missing first teleport code'
    print(f'\033[92mCode #6: {m.group(1)}\033[0m: {md5(m.group(1))}')

    vm, descs, known_locs = find_and_collect_all(vm, known_locs)

    print('>> Using teleporter again')
    vm.patch_teleporter_call()
    vm.registers[7] = 25734
    vm.send('use teleporter')

    data = vm.read()
    m = re.search(
        r'Someone seems to have drawn a message in the sand here:\n\s+(.*?)\n',
        data
    )
    assert m, 'Missing second teleport code'
    print(f'\033[92mCode #7: {m.group(1)}\033[0m: {md5(m.group(1))}')

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
        code = reflect(m.group(1))
        print('\033[92mCode #8: ' + code + f'\033[0m: {md5(code)}')
    else:
        print('\033[91mError! Last code not found\033[0m')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-b',
        '--binfile',
        default='challenge.bin',
        help='Path to challenge.bin',
    )
    parser.add_argument(
        '-a',
        '--archfile',
        default='arch-spec',
        help='Path to arch-spec',
    )
    args = parser.parse_args()

    solve_all(args.archfile, args.binfile)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
