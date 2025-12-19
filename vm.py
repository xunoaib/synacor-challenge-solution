import ast
import pickle
import re
import readline
from copy import deepcopy
from itertools import pairwise, zip_longest
from pathlib import Path
from typing import Any, override

from basevm import BaseVM, Registers
from disassembler import disassemble

ALIASES = {
    'l': 'look',
    'n': 'north',
    's': 'south',
    'e': 'east',
    'w': 'west',
    'br': 'bridge',
    'dw': 'doorway',
    'dn': 'down',
    'cn': 'continue',
    'pa': 'passage',
}

SNAPSHOTS_DIR = Path('snapshots')


class VM(BaseVM):

    SNAPSHOT_ATTRS = [
        'memory',
        'stack',
        'registers',
        'pc',
        'input_buffer',
        'output_buffer',
        'location_addr',
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.location_addr = None
        self.teleport_call_addr = None

    def interactive(self):
        try:
            while True:
                self.run()
                print(self.read(), end='')
                self.send(input('\033[93;1mdbg>\033[0m '))
        except EOFError:
            pass

    @override
    def __repr__(self):
        return f'<{self.__class__.__name__}(pc={self.pc}, loc={self.location})>'

    # =================
    # Location Tracking
    # =================

    @property
    def location(self):
        if self.location_addr is None:
            print('===== Calculating Location Address ======')
            self.location_addr = calculate_location_addr(self)

        assert self.location_addr is not None, 'Location address not set'
        return self.memory[self.location_addr]

    @location.setter
    def location(self, value: int):
        assert self.location_addr is not None, 'Location address not set'
        self.memory[self.location_addr] = value

    # ==============
    # Input Handling
    # ==============

    def sendcopy(self, cmd) -> 'VM':
        '''Sends a command to a copy of the current VM, returning the new VM'''

        vm = self.clone()
        vm.send(cmd)
        return vm

    @override
    def send(self, cmd) -> None:
        if ';' in cmd:
            # prevent these from interfering with breakpoints?
            for subcmd in cmd.split(';'):
                self.send(subcmd.strip())
            return

        # intercept special debug commands
        if cmd.startswith('.'):
            try:
                debug_cmd(self, cmd[1:])
            except Exception as exc:
                print('Error:', exc)
                raise exc
            return

        if newcmd := ALIASES.get(cmd):
            print(f'# aliased {cmd} => {newcmd}')
            cmd = newcmd

        super().send(cmd)

    def sendread(self, cmd) -> str:
        self.read()  # discard old output
        self.send(cmd)  # run command
        return self.read()  # return new output

    # ======================
    # Teleportation Patching
    # ======================

    @override
    def execute(self, opcode, args):
        # skip slow call but set the proper post-exec values
        if opcode.name == 'call' and args[0] == self.teleport_call_addr:
            self.pc += len(opcode)
            self.registers[0] = 6
            self.registers[1] = 5
            self.registers[7] = 25734  # secret value
            return True
        return super().execute(opcode, args)

    def patch_teleporter_call(self):
        self.teleport_call_addr = find_teleporter_call(self.memory)

    # ============
    # Snapshotting
    # ============

    def deserialize(self, data: bytes):
        return self.from_snapshot(pickle.loads(data))

    def serialize(self) -> bytes:
        return pickle.dumps(self.snapshot())

    def snapshot(self):
        return {k: deepcopy(getattr(self, k)) for k in self.SNAPSHOT_ATTRS}

    @classmethod
    def from_snapshot(cls, snapshot: dict):
        return cls().apply_snapshot(snapshot)

    def apply_snapshot(self, snapshot: dict):
        for attrib, value in snapshot.items():
            setattr(self, attrib, value)
        return self

    def clone(self):
        return deepcopy(self)


def debug_cmd(vm: VM, cmd: str):
    match cmd.split():
        case ['dump']:
            print(repr(vm))

        case ['dump', fname]:
            if Path(fname).exists():
                if input(f'{fname} already exists. Overwrite? [y/N] ') != 'y':
                    return
            with open(fname, 'w') as f:
                f.write(repr(vm))
            print('saved to', fname)

        case ['pc']:
            print('pc =', vm.pc)

        case ['save', *fname]:
            fname = fname or ['last']
            directory = SNAPSHOTS_DIR
            directory.mkdir(exist_ok=True)
            fname = directory / fname[0]
            with open(fname, 'wb') as f:
                f.write(vm.serialize())
            print('saved snapshot to', fname)

        case ['load', fname]:
            fname = SNAPSHOTS_DIR / fname
            with open(fname, 'rb') as f:
                data = f.read()
                vm.apply_snapshot(pickle.loads(data))
            print('restored snapshot from', fname)

        case ['diff', fname1, *fnames]:
            directory = SNAPSHOTS_DIR
            vm1 = vm.from_snapshot_file(directory / fname1)
            if fnames:
                vm2 = vm.from_snapshot_file(directory / fnames[0])
            else:
                vm2 = vm
            diffs = diff_vms(vm1, vm2)
            __import__('pprint').pprint(diffs)

        case ['giveall']:
            # give all known items (note: these addrs vary between binaries)
            for addr in range(2670, 2734 + 1, 4):
                vm.memory[addr] = 0

        # write value to the STACK at address (0 = the bottom)
        case ['ws', addr, val]:
            vm.stack[int(addr)] = int(val)

        # write value to MEMORY at address (0 = the bottom)
        case ['wm', addr, val]:
            vm.memory[int(addr)] = int(val)

        # write value to register
        case ['wr', addr, val]:
            vm.registers[int(addr)] = int(val)

        # print memory
        case ['pm', addr, *nbytes]:
            addr = int(addr)
            nbytes = int(nbytes[0]) if nbytes else 1
            print(vm.memory[addr:addr + nbytes])

        case ['reg']:
            print(vm.registers)

        case ['ps', addr, *nbytes]:
            addr = int(addr)
            nbytes = int(nbytes[0]) if nbytes else 1
            print(vm.stack[addr:addr + nbytes])

        case ['pinv']:
            for addr in range(2670, 2734 + 1, 4):
                print(addr, vm.memory[addr:addr + 4])

        case ['loc']:
            print(vm.location)

        case ['loc', newloc]:
            print('changing location to:', newloc)
            vm.location = int(newloc)

        case ['dis']:
            disassemble(vm.memory, vm.pc, 15)

        case ['dis', lines]:
            disassemble(vm.memory, vm.pc, int(lines))

        case ['dis', lines, addr]:
            disassemble(vm.memory, int(addr), int(lines))

        case ['solve', 'coins']:
            coins = [
                'blue coin',
                'red coin',
                'shiny coin',
                'concave coin',
                'corroded coin',
            ]
            for coin in coins:
                vm.send('use ' + coin)
            vm.run()

        case ['macro', fname]:
            fname = Path('macros') / fname
            print('running macros from:', fname)
            with open(fname) as f:
                commands = re.split(r'[\n;]+', f.read().strip())

            for i, cmd in enumerate(commands):
                print(
                    f'\033[93m>>> [{i}/{len(commands)}] sending "{cmd}"\033[0m'
                )
                vm.send(cmd)
                print(vm.read())

        case ['quit' | 'q']:
            exit()

        case _:
            print('unknown debug command')


def diff_snapshots(snap1: dict, snap2: dict):
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


def diff_vms(v1: VM, v2: VM):
    return diff_snapshots(v1.snapshot(), v2.snapshot())


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


def calculate_location_addr(vm: VM):
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
