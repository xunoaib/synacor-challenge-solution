import ast
import re
import readline
from pathlib import Path
from typing import override

from colorama import Fore, Style

import utils
from basevm import BaseVM

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


class VM(BaseVM):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.teleport_call_addr: int | None = None

    @override
    def input(self):
        cmd = input(Fore.YELLOW + Style.BRIGHT + 'dbg> ' + Style.RESET_ALL)
        self.send(cmd)

    def sendcopy(self, cmd):
        '''Sends a command to a copy of the current VM and returns the new VM'''

        vm = self.clone()
        vm.send(cmd)
        return vm

    @override
    def send(self, cmd):
        if ';' in cmd:
            # prevent these from interfering with breakpoints?
            for subcmd in cmd.split(';'):
                self.send(subcmd.strip())
            return

        # intercept special debug commands
        if cmd.startswith('.'):
            debug_cmd(self, cmd[1:])
            return

        if newcmd := ALIASES.get(cmd):
            if self.is_interactive:
                print(f'# aliased {cmd} => {newcmd}')
            cmd = newcmd

        super().send(cmd)

    def sendread(self, cmd):
        self.read()
        self.send(cmd)
        return self.read()

    @override
    def execute(self, opcode, args):
        # skip slow call but set the proper post-exec values
        if opcode.name == 'call' and args[0] == self.teleport_call_addr:
            self.pc += len(opcode)
            self.registers[0] = 6
            self.registers[1] = 5
            self.registers[7] = 25734  # secret value
            return self.get_next_instruction()
        return super().execute(opcode, args)

    def patch_teleporter_call(self):
        self.teleport_call_addr = utils.find_teleporter_call(self.memory)


def debug_cmd(vm: VM, cmd: str):
    match cmd.split():
        case ['ticks']:
            print(f'ticks = {vm.ticks}')

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
            if not fname:
                fname = ['last']
            directory = Path('snapshots')
            directory.mkdir(exist_ok=True)
            fname = directory / fname[0]
            with open(fname, 'w') as f:
                f.write(str(vm.snapshot()))
            print('saved snapshot to', fname)

        case ['load', fname]:
            fname = Path('snapshots') / fname
            with open(fname) as f:
                snapshot = ast.literal_eval(f.read())
            vm.load_snapshot(snapshot)
            print('restored snapshot from ', fname)

        case ['diff', fname1, *fnames]:
            directory = Path('snapshots')
            vm1 = vm.from_snapshot_file(directory / fname1)
            if fnames:
                vm2 = vm.from_snapshot_file(directory / fnames[0])
            else:
                vm2 = vm
            diffs = utils.diff_vms(vm1, vm2)
            __import__('pprint').pprint(diffs)

        case ['giveall']:
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
            from disassembler import disassemble
            disassemble(vm.memory, vm.pc, 15)

        case ['dis', lines]:
            from disassembler import disassemble
            disassemble(vm.memory, vm.pc, int(lines))

        case ['dis', lines, addr]:
            from disassembler import disassemble
            disassemble(vm.memory, int(addr), int(lines))

        case ['solve', 'coins']:
            coins = [
                'blue coin', 'red coin', 'shiny coin', 'concave coin',
                'corroded coin'
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
                    Fore.YELLOW + f'>>> [{i}/{len(commands)}] sending "{cmd}"'
                    + Style.RESET_ALL
                )
                vm.send(cmd)
                print(vm.read())

        case ['quit' | 'q']:
            exit()

        case _:
            print('unknown debug command')
