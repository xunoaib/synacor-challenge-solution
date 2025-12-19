import re
import string
from dataclasses import dataclass
from itertools import pairwise, zip_longest

from rich.console import Console
from rich.table import Table


@dataclass
class Opcode:
    name: str
    id: int
    nargs: int

    def __len__(self):
        return 1 + self.nargs


def load_bytecode(fname):
    with open(fname, 'rb') as f:
        data = f.read()

    return [
        int.from_bytes(data[i:i + 2], 'little')
        for i in range(0, len(data), 2)
    ]


def isreg(arg):
    return arg >= 32768


def to_register(arg):
    return arg - 32768 if isreg(arg) else arg


def read_instruction(memory, addr):
    opid = memory[addr]
    opcode = OPCODES[opid]
    args = tuple(memory[addr + 1:addr + 1 + opcode.nargs])
    return opcode, args


def parse_opcodes():
    with open('arch-spec') as f:
        data = f.read()

    opcodes = {}
    for name, opid, args in re.findall(r'(.*): (\d+)(.*?)\n', data):
        nargs = len(args.strip().split())
        opid = int(opid)
        opcodes[opid] = Opcode(name, opid, nargs)
    return opcodes


OPCODES = parse_opcodes()


def diff_snapshot(snap1, snap2):
    diff_result = {}
    for key in snap1:
        v1 = snap1[key]
        v2 = snap2[key]

        if v1 == v2:
            continue

        if isinstance(v1, list):
            diff_result[key] = [
                (idx, subv1, subv2)
                for idx, (subv1, subv2) in enumerate(zip_longest(v1, v2))
                if subv1 != subv2
            ]
        else:
            diff_result[key] = (v1, v2)
    return diff_result


def diff_vms(v1, v2):
    return diff_snapshot(v1.snapshot(), v2.snapshot())


def rprint_diff(diff):
    console = Console()
    for section, vals in diff.items():
        table = diff_table(vals, section.capitalize())
        console.print(table)


def diff_table(section_data, title):
    table = Table(title=title)
    for col in ('Loc', 'Old', 'New'):
        table.add_column(col, justify='right')

    for vals in section_data:
        vals = list(vals)
        for i, v in enumerate(vals):
            if v < 256 and chr(v) in string.printable:
                vals[i] = f"'[bold green]{chr(v)}[/bold green]' {v}"
        table.add_row(*map(str, vals))
    return table


def find_code(memory: list[int], code: list[int | None]):
    n = len(code)
    return [
        i for i in range(len(memory))
        if all(m == c for m, c in zip(memory[i:i + n], code) if c is not None)
    ]


def find_teleporter_call(memory: list[int]):

    # Code to search for (ignoring special memory addresses)
    code = [
        7, 32768, None, 9, 32768, 32769, 1, 18, 7, 32769, None, 9, 32768,
        32768, 32767, 1, 32769, 32775, 17, None, 18, 2, 32768, 9, 32769, 32769,
        32767, 17, None, 1, 32769, 32768, 3, 32768, 9, 32768, 32768, 32767, 17,
        None, 18
    ]

    addrs = find_code(memory, code)
    assert len(addrs) == 1, f'Found multiple teleporter calls ({len(addrs)})'
    return addrs[0]


def calculate_location_addr(vm: 'EnhancedCPU'):
    print('Calculating location address')
    vm = vm.clone()
    vm.run()
    vms = [vm]

    for cmd in ['doorway', 'north', 'north']:
        vms.append(vms[-1].sendcopy(cmd))

    loc_addr = None
    for a, b in pairwise(vms):
        diff = diff_vms(a, b)
        assert 'memory' in diff, 'Diff does not contain memory'
        mem = diff['memory']
        addrs = [d[0] for d in mem]
        loc_addr = addrs[0]  # assume lowest (may be incorrect)

    assert loc_addr
    return loc_addr
