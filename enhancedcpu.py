import ast
import re
import readline
import sys
from pathlib import Path
from functools import cache

from cpu import CPU
import utils
from disassembler import format_instruction

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

class EnhancedCPU(CPU):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.call_cache = {}
        self.call_stack = []

        # list of condition funcs and corresponding pre/post hooks to call
        self.hooks = [
            (call_condition, call_pre_hook, call_post_hook)
        ]

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

                # write value to register
                case ['wr', addr, val]:
                    self.registers[int(addr)] = int(val)

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

                case ['dis']:
                    from disassembler import disassemble
                    disassemble(self.memory, self.pc, 15)

                case ['dis', lines]:
                    from disassembler import disassemble
                    disassemble(self.memory, self.pc, int(lines))

                case ['dis', lines, addr]:
                    from disassembler import disassemble
                    disassemble(self.memory, int(addr), int(lines))

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
                        commands = re.split(r'[\n;]+', f.read().strip())

                    for i, cmd in enumerate(commands):
                        print(Fore.YELLOW + f'>>> [{i}/{len(commands)}] sending "{cmd}"' + Style.RESET_ALL)
                        self.send(cmd)
                        print(self.read())

                case ['quit' | 'q']:
                    exit()

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
            # prevent these from interfering with breakpoints?
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

    # @override
    def execute(self, opcode, args):
        # print(self.pc, format_instruction(opcode,args))

        # run pre-hooks
        for hook_condition, pre_hook, _ in list(self.hooks):
            if hook_condition(self):
                pre_hook(self)

        if opcode.name == 'call':

            # # skip call 6027 but set the proper post-exec values
            if args[0] == 6027:
                self.pc += len(opcode)
                self.registers[0] = 6
                self.registers[1] = 5
                self.registers[7] = 25734  # secret value
                return self.get_next_instruction()
            # else:
            #     self.call_stack.append(
            #         lambda after, before=self.registers.copy():
            #         my_ret_hook(before, after)
            #     )
            pass

        # when a call returns, run the correspondng ret hook to cache the return values (if needed)
        elif opcode.name == 'ret':
            if not self.call_stack:
                pass
            elif ret_hook := self.call_stack.pop():
                ret_hook(self.registers)

        result = super().execute(opcode, args)

        for hook_condition, _, post_hook in list(self.hooks):
            if hook_condition(self):
                post_hook(self)

        return result

def my_ret_hook(rv_before, rv_after):
    return
    idxs = (0,1)
    print([rv_before[i] for i in idxs])
    print([rv_after[i] for i in idxs])
    print()


def my_call_6027(r0, r1, r7):
    if r0 == 0:
        return r1 + 1

    if r1 == 0:
        return my_call_6027(r0 - 1, r7, r7) # a : runs b and c from r1 = (r7 to 0)

    # n0 = my_call_6027(r0, r1 - 1, r7) # b : goes from r1 to 0
    # return my_call_6027(r0 - 1, n0, r7)  # c :

    return my_call_6027(
        r0 = r0 - 1,
        r1 = my_call_6027(r0, r1 - 1, r7),
        r7 = r7
    )

# ------------------------------

def split_6027(r0, r1, r7):
    if r0 == 0:
        return r1 + 1, r1

    if r1 == 0:
        return func_a(r0 - 1, r7, r7) # a : runs b and c from r1 = (r7 to 0)

    n0, _ = func_b(r0, r1 - 1, r7) # b : goes from r1 to 0
    return func_c(r0 - 1, n0, r7)  # c :


func_a = lambda r0, _,r7: split_6027(r0 - 1, r7, r7)
func_b = lambda r0,r1,r7: split_6027(r0, r1 - 1, r7)
func_c = lambda r0,r1,r7: split_6027(r0 - 1, r1, r7)

def gen_ret_hook(rv_in):
    '''
    Returns a function that caches the current register values for a given input.
    Maps rv_in to 'rv_out' whose values are auto retrieved from the cpu.
    '''

    def write_cache(cpu):
        rv_out = (cpu.r0, cpu.r1, cpu.r7)
        cpu.call_cache[rv_in] = rv_out
        return rv_out

    return write_cache

# ------------------------------

def ret_condition(cpu: EnhancedCPU):
    '''Returns true if the current instruction is a call'''

    opcode, _ = cpu.get_next_instruction()
    return opcode.name == 'ret'

def ret_pre_hook(cpu):
    # simply print registers
    inst = format_instruction(*cpu.get_next_instruction())
    # print(inst, cpu.registers, file=sys.stderr)

def ret_post_hook(cpu):
    ...

# ------------------------------

def call_condition(cpu: EnhancedCPU):
    '''Returns true if the current instruction is a call'''

    opcode, _ = cpu.get_next_instruction()
    return opcode.name == 'call'

def call_pre_hook(cpu):
    # simply print registers
    inst = format_instruction(*cpu.get_next_instruction())
    # print(inst, cpu.registers, file=sys.stderr)

def call_post_hook(cpu):
    ...
