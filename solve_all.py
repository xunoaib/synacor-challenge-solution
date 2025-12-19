import argparse
import hashlib
import re
from pathlib import Path
from typing import Any, Callable

from plot_maps import plot_edges, plot_edges_interactive
from vm import VM, diff_vms


def md5(s: str):
    return hashlib.md5(s.encode()).hexdigest()


def reflect(s: str):
    d = {'d': 'b', 'p': 'q'}
    d |= {v: k for k, v in d.items()}
    return ''.join(d.get(c, c) for c in s)[::-1]


def neighbor_locs(vm: VM) -> list[tuple[str, VM]]:
    return [(dir, vm.sendcopy(dir)) for dir in find_exits(vm)]


def find_exits(vm: VM):
    vm = vm.clone()
    vm.read()
    vm.send('look')
    m = re.search(
        r'\nThere (is|are) (\d+) exits?:\n(.*)\nWhat do you do?', vm.read(),
        re.DOTALL
    )
    return re.findall(r'- (.*?)\n', m.group(3)) if m else []


def find_items(vm: VM):
    vm = vm.clone()
    vm.read()
    vm.send('look')
    m = re.search(
        r'\nThings of interest here:\n(.*?)\n\n', vm.read(), re.DOTALL
    )
    return re.findall(r'- (.*?)\n', m.group(1) + '\n') if m else []


def identify_item_addrs(vms: list[VM]):
    addrs = {}
    for vm in vms:
        for item in find_items(vm):
            vm2 = vm.sendcopy('take ' + item)
            result = diff_vms(vm, vm2)
            addr = next(
                idx for idx, old, new in result.get('memory', [])
                if old and not new
            )
            addrs[item] = addr
    return addrs


def explore(vm: VM):
    vm.read()
    vm.send('look')

    vms: dict[int, VM] = {}
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


def print_new_locs(known_locs: dict[int, VM], vms: dict[int, VM]):
    for loc in set(vms) - set(known_locs):
        v = vms[loc]
        v.read()
        d = v.sendcopy('look').read()
        if m := re.search(r'== (.*?) ==', d):
            d = m.group(1)
        print(f'New location: {loc} ({d})')


def find_all_states(vm: VM):
    edges, descs, vms = explore(vm)
    item_addrs = identify_item_addrs(list(vms.values()))
    print(f'Found {len(vms)} states and {len(item_addrs)} items\n')
    return edges, descs, vms, item_addrs


def take_all_items(vm: VM, item_addrs: dict[str, int]):
    vm = vm.clone()
    print()
    for name, addr in item_addrs.items():
        print(f'Giving mem[{addr}] = {name}')
        vm.memory[addr] = 0
    print()
    return vm


def find_and_collect_all(vm: VM, known_locs: dict[int, VM]):
    edges, descs, vms, item_addrs = find_all_states(vm)
    print_new_locs(known_locs, vms)
    vm = take_all_items(vm, item_addrs)
    return edges, vm, descs, known_locs | vms


def print_code(num: int, code: str):
    print(f'\033[92mCode #{num}: {code}\033[0m: {md5(code)}')


def solve_all(
    arch_spec_fname, challenge_bin_fname,
    plot: Callable[[dict[int, Any], dict[int, Any], str], None] | None
):
    print(f'\033[93mLoading arch-spec: {arch_spec_fname}\033[0m')
    with open(arch_spec_fname) as f:
        data = f.read()

    m1 = re.search("Here's a code for the challenge website: (.*?)\n", data)
    assert m1, 'Missing arch-spec code'
    print_code(1, m1.group(1))

    print(f'\033[93mLoading binary: {challenge_bin_fname}\033[0m')

    vm = VM(challenge_bin_fname)
    vm.run()
    data = vm.read()

    m2 = re.search('this one into the challenge website: (.*?)\n', data)
    assert m2, 'Missing pre-test code'
    print_code(2, m2.group(1))

    m3 = re.search('The self-test completion code is: (.*?)\n', data)
    assert m3, 'Missing post-test code'
    print_code(3, m3.group(1))

    edges, vm, descs, known_locs = find_and_collect_all(vm, {})
    plot and plot(edges, descs, 'map0')

    vm.send('use can')
    vm.send('use lantern')
    vm.send('use tablet')

    print('\033[93m>> Using tablet\033[0m')
    m = re.search(
        r'You find yourself writing "(.*?)" on the tablet', vm.read()
    )
    assert m, 'Missing tablet code'
    print_code(4, m.group(1))

    print('\033[93m>> Solving twisty maze\033[0m')

    edges, vm, descs, known_locs = find_and_collect_all(vm, known_locs)
    plot and plot(edges, descs, 'map1')

    code5 = next(
        (
            m.group(1) for d in descs.values()
            if (m := re.search('Chiseled on the wall.*\n\n    (.*?)\n', d))
        ), None
    )
    assert code5, 'Missing maze code'
    print_code(5, code5)

    # Go to central hall
    vm.location = next(
        loc for loc, desc in descs.items() if
        'There is a strange monument in the center of the hall with circular slots and unusual'
        in desc
    )

    print('\033[93m>> Solving coins puzzle\033[0m')
    vm.send('use blue coin')
    vm.send('use red coin')
    vm.send('use shiny coin')
    vm.send('use concave coin')
    vm.send('use corroded coin')

    edges, vm, descs, known_locs = find_and_collect_all(vm, known_locs)
    plot and plot(edges, descs, 'map2')

    print('\033[93m>> Using teleporter\033[0m')
    vm.send('use teleporter')
    m = re.search(
        r'you think you see a pattern in the stars...\n\s+(.*?)\n', vm.read()
    )
    assert m, 'Missing first teleport code'
    print_code(6, m.group(1))

    edges, vm, descs, known_locs = find_and_collect_all(vm, known_locs)
    plot and plot(edges, descs, 'map3')

    print('\033[93m>> Using teleporter again\033[0m')
    vm.patch_teleporter_call()
    vm.registers[7] = 25734
    vm.send('use teleporter')

    m = re.search(
        r'Someone seems to have drawn a message in the sand here:\n\s+(.*?)\n',
        vm.read()
    )
    assert m, 'Missing second teleport code'
    print_code(7, m.group(1))

    edges, vm, descs, known_locs = find_and_collect_all(vm, known_locs)
    plot and plot(edges, descs, 'map4')

    print('\033[93m>> Solving antechamber\033[0m')
    vm.location = next(
        loc for loc, desc in descs.items() if '== Vault Antechamber ==' in desc
    )

    vm.send('look')
    vm.send('take orb')
    vm.send('n;e;e;n;w;s;e;e;w;n;n;e')
    vm.send('vault')
    vm.send('take mirror')
    vm.read()
    vm.send('use mirror')

    m = re.search(
        'Through the mirror, you see "(.*)" scrawled in charcoal', vm.read()
    )
    assert m, 'Missing mirror code'
    print_code(8, reflect(m.group(1)))

    edges, vm, descs, known_locs = find_and_collect_all(vm, known_locs)
    plot and plot(edges, descs, 'map5')


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
    parser.add_argument(
        '-d',
        '--dir',
        default='.',
        help='Path to directory containing challenge files',
    )
    parser.add_argument(
        '-p',
        '--map-format',
        choices=['png', 'html'],
    )
    args = parser.parse_args()

    archfile = Path(args.dir) / args.archfile
    binfile = Path(args.dir) / args.binfile

    mapdir = Path('maps')
    mapdir.mkdir(exist_ok=True)

    plot_funcs = {
        'png':
        lambda edges, descs, name: plot_edges(
            edges, descs, fname=str(mapdir / f'{name}.png'), show=False
        ),
        'html':
        lambda edges, descs, name: plot_edges_interactive(
            edges, descs, fname=str(mapdir / f'{name}.html')
        ),
    }

    plot = plot_funcs.get(args.map_format, None)

    solve_all(archfile, binfile, plot)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
