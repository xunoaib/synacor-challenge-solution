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
        directory = Path('snapshots')
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

                case ['save', *fname]:
                    if not fname:
                        fname = ['last']
                    directory.mkdir(exist_ok=True)
                    fname = directory / fname[0]
                    with open(fname, 'w') as f:
                        f.write(str(self.snapshot()))
                    print('saved snapshot to', fname)

                case ['load', fname]:
                    print(f'restoring snapshot "{fname}"')
                    with open(directory / fname) as f:
                        snapshot = ast.literal_eval(f.read())
                    self.load_snapshot(snapshot)

                case ['diff', fname1, *fnames]:
                    with open(directory / fname1) as f:
                        snap1 = ast.literal_eval(f.read())

                    if fnames:
                        with open(directory / fnames[0]) as f:
                            snap2 = ast.literal_eval(f.read())
                    else:
                        snap2 = self.snapshot()

                    diffs = utils.diff_snapshot(snap1, snap2)
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

                case ['dis', addr]:
                    from disassembler import disassemble
                    disassemble(self.memory, int(addr))

                case _:
                    print('unknown debug command')

        except Exception as exc:
            print(exc)

    def input(self):
        cmd = input(Fore.YELLOW + Style.BRIGHT + 'dbg> ' + Style.RESET_ALL)
        self.send(cmd)

    # @override
    def send(self, cmd):
        # intercept special debug commands
        if cmd.startswith('.'):
            self.debug_cmd(cmd[1:])
            return True

        if newcmd := ALIASES.get(cmd):
            print(f'# aliased {cmd} => {newcmd}')
            cmd = newcmd

        super().send(cmd)
