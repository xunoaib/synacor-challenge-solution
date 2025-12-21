import re
from dataclasses import dataclass
from itertools import batched
from typing import override


@dataclass
class Opcode:
    name: str
    id: int
    nargs: int

    def __len__(self):
        return 1 + self.nargs


def is_reg(arg: int):
    return arg >= 32768


def to_reg(arg: int):
    return arg - 32768 if is_reg(arg) else arg


def read_instruction(memory: list[int], addr: int):
    opcode = OPCODES[memory[addr]]
    args = tuple(memory[addr + 1:addr + 1 + opcode.nargs])
    return opcode, args


def parse_opcodes(arch_spec='arch-spec') -> dict[int, Opcode]:
    '''Parse opcodes and their expected arguments from the arch-spec document'''

    with open(arch_spec) as f:
        data = f.read()

    opcodes = {}
    for name, opid, args in re.findall(r'(.*): (\d+)(.*?)\n', data):
        nargs = len(args.strip().split())
        opid = int(opid)
        opcodes[opid] = Opcode(name, opid, nargs)
    return opcodes


OPCODES = parse_opcodes()


def load_bytecode(binfile):
    with open(binfile, 'rb') as f:
        return [int.from_bytes(b, 'little') for b in batched(f.read(), 2)]


class Registers:

    def __init__(self, regs=None):
        self._regs = regs if regs else [0] * 8

    def __getitem__(self, idx) -> int:
        return self._regs[idx]

    def __setitem__(self, idx, val):
        self._regs[idx] = val

    @override
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self._regs})'

    @override
    def __eq__(self, other):
        assert isinstance(
            other, self.__class__
        ), f'Unexpected class: {type(other)}'
        return self._regs == other._regs

    def __iter__(self):
        return iter(self._regs)

    def __len__(self):
        return len(self._regs)


class BaseVM:

    def __init__(self, binfile=None):
        self.memory = []
        self.registers = Registers()
        self.stack: list[int] = []
        self.pc: int = 0
        self.input: list[str] = []
        self.output: str = ''

        if binfile:
            self.memory = load_bytecode(binfile)

    def value(self, arg) -> int:
        return self.registers[arg - 32768] if is_reg(arg) else arg

    def set_reg(self, arg, value):
        self.registers[to_reg(arg)] = value

    def send(self, cmd) -> 'BaseVM':
        self.input = list(cmd + '\n')
        self.run()
        return self

    def read(self):
        result = self.output
        self.output = ''
        return result

    def flush(self):
        self.read()
        return self

    def run(self):
        while self.step():
            pass
        return self

    def step(self) -> bool:
        '''Returns False if halted or waiting for input'''
        return self.execute(*read_instruction(self.memory, self.pc))

    def execute(self, opcode: Opcode, args: tuple[int, ...]):
        '''Executes the given instruction and returns False if halted or
        waiting for input'''

        new_pc = self.pc + len(opcode)
        a, b, c = args + (0, ) * (3 - len(args))

        match opcode.name:
            case 'noop':
                pass

            case 'halt':
                return False

            case 'out':
                self.output += chr(self.value(a))

            case 'jmp':
                new_pc = a

            case 'jt':
                if self.value(a) != 0:
                    new_pc = b

            case 'jf':
                if self.value(a) == 0:
                    new_pc = b

            case 'set':
                self.set_reg(a, self.value(b))

            case 'add':
                self.set_reg(a, (self.value(b) + self.value(c)) % 32768)

            case 'eq':
                self.set_reg(a, int(self.value(b) == self.value(c)))

            case 'push':
                self.stack.append(self.value(a))

            case 'pop':
                self.set_reg(a, self.stack.pop())

            case 'gt':
                self.set_reg(a, int(self.value(b) > self.value(c)))

            case 'and':
                self.set_reg(a, int(self.value(b) & self.value(c)))

            case 'or':
                self.set_reg(a, int(self.value(b) | self.value(c)))

            case 'not':
                self.set_reg(a, ~self.value(b) & (2**15 - 1))

            case 'call':
                self.stack.append(new_pc)
                new_pc = self.value(a)

            case 'mult':
                self.set_reg(a, (self.value(b) * self.value(c)) % 32768)

            case 'mod':
                self.set_reg(a, self.value(b) % self.value(c))

            # read memory at address <b> and write it to <a>
            case 'rmem':
                self.set_reg(a, self.memory[self.value(b)])

            # write the value from <b> into memory at address <a>
            case 'wmem':
                self.memory[self.value(a)] = self.value(b)

            # remove the top element from the stack and jump to it; empty stack = halt
            case 'ret':
                if not self.stack:
                    return False
                new_pc = self.stack.pop()

            case 'in':
                # pause program when input buffer is empty
                if not self.input:
                    return False

                self.set_reg(a, ord(self.input.pop(0)))

            case _:
                raise NotImplementedError(
                    f'Not implemented: {opcode=} {args=}'
                )

        self.pc = new_pc
        return True
