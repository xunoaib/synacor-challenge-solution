import ast
import readline
from pathlib import Path

from cpu import CPU
import utils

from colorama import Style, Fore

ALIASES = {
    'l':'look',
    'n':'north',
    's':'south',
    'e':'east',
    'w':'west',
    'br':'bridge',
    'dw':'doorway',
    'dn':'down',
    'cn':'continue',
    'pa':'passage',
}

class Debugger(CPU):
    def debug_cmd(self, cmd):
        try:
            match cmd.split():
                case ['dump']:
                    print(repr(self))

                case ['dump', fname]:
                    if Path(fname).exists():
                        if input(f'{fname} already exists. Overwrite? [y/N] ') != 'y':
                            return
                    with open(fname, 'w') as f:
                        f.write(repr(self))
                    print('saved to', fname)

                case ['pc']:
                    print('pc =', self.pc)

                case ['save', *fname]:
                    if not fname:
                        fname = ['last']
                    directory = Path('snapshots')
                    directory.mkdir(exist_ok=True)
                    fname = directory / fname[0]
                    with open(fname, 'w') as f:
                        f.write(str(self.snapshot()))
                    print('saved snapshot to', fname)

                case ['load', fname]:
                    fname = Path('snapshots') / fname
                    with open(fname) as f:
                        snapshot = ast.literal_eval(f.read())
                    self.load_snapshot(snapshot)
                    print('restored snapshot from ', fname)

                case ['diff', fname1, *fnames]:
                    directory = Path('snapshots')
                    vm1 = self.from_snapshot_file(directory / fname1)
                    if fnames:
                        vm2 = self.from_snapshot_file(directory / fnames[0])
                    else:
                        vm2 = self
                    diffs = utils.diff_vms(vm1, vm2)
                    __import__('pprint').pprint(diffs)

                case ['giveall']:
                    for addr in range(2670, 2734+1, 4):
                        self.memory[addr] = 0

                # write value to the STACK at address (0 = the bottom)
                case ['ws', addr, val]:
                    self.stack[int(addr)] = int(val)

                # write value to MEMORY at address (0 = the bottom)
                case ['wm', addr, val]:
                    self.memory[int(addr)] = int(val)

                # print memory
                case ['pm', addr, *nbytes]:
                    addr = int(addr)
                    nbytes = int(nbytes[0]) if nbytes else 1
                    print(self.memory[addr:addr+nbytes])

                case ['reg']:
                    print(self.registers)

                case ['ps', addr, *nbytes]:
                    addr = int(addr)
                    nbytes = int(nbytes[0]) if nbytes else 1
                    print(self.stack[addr:addr+nbytes])

                case ['pinv']:
                    for addr in range(2670, 2734+1, 4):
                        print(addr, self.memory[addr:addr+4])

                case ['loc']:
                    print(self.location)

                case ['loc', newloc]:
                    print('changing location to:', newloc)
                    self.location = int(newloc)

                case ['dis', addr]:
                    from disassembler import disassemble
                    disassemble(self.memory, int(addr))

                case ['solve', 'coins']:
                    coins = [
                        'blue coin',
                        'red coin',
                        'shiny coin',
                        'concave coin',
                        'corroded coin'
                    ]
                    for coin in coins:
                        self.send('use ' + coin)
                    self.run()

                case ['macro', fname]:
                    fname = Path('macros') / fname
                    print('running macros from:', fname)
                    with open(fname) as f:
                        commands = f.read().strip().splitlines()

                    for cmd in commands:
                        print(f'>>> sending "{cmd}"')
                        self.send(cmd)

                case _:
                    print('unknown debug command')

        except Exception as exc:
            print(exc)

    # @override
    def input(self):
        cmd = input(Fore.YELLOW + Style.BRIGHT + 'dbg> ' + Style.RESET_ALL)
        self.send(cmd)

    def sendcopy(self, cmd):
        '''Sends a command to a copy of the current VM and returns the new VM'''

        vm = self.clone()
        vm.send(cmd)
        return vm

    # @override
    def send(self, cmd):
        if ';' in cmd:
            for subcmd in cmd.split(';'):
                self.send(subcmd.strip())
            return

        # intercept special debug commands
        if cmd.startswith('.'):
            self.debug_cmd(cmd[1:])
            return True

        if newcmd := ALIASES.get(cmd):
            print(f'# aliased {cmd} => {newcmd}')
            cmd = newcmd

        super().send(cmd)
