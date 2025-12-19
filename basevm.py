import ast
import copy
from typing import Any, override

from utils import (calculate_location_addr, is_reg, load_bytecode,
                   read_instruction, to_reg)


class Registers:

    def __init__(self):
        self._regs = [0] * 8

    def __getitem__(self, idx):
        return self._regs[idx]

    def __setitem__(self, idx, val):
        self._regs[idx] = val


class BaseVM:

    SNAPSHOT_ATTRS = [
        'memory',
        'stack',
        'registers',
        'pc',
        'input_buffer',
        'output_buffer',
        'location_addr',
    ]

    def __init__(self, binfile=None):
        self.memory = []
        self.registers = Registers()
        self.stack = []
        self.pc = 0  # program counter
        self.input_buffer = []  # keyboard input buffer
        self.output_buffer = ''
        self.ticks = 0
        self.location_addr: int | None = None
        self.is_interactive = False

        if binfile:
            self.load_program(binfile)

    def load_program(self, binfile):
        self.memory = load_bytecode(binfile)
        self.pc = 0
        self.location_addr = calculate_location_addr(self)

    def value(self, arg):
        return self.registers[arg - 32768] if is_reg(arg) else arg

    @property
    def location(self):
        assert self.location_addr is not None, 'Location address not set'
        return self.memory[self.location_addr]

    @location.setter
    def location(self, value: int):
        assert self.location_addr is not None, 'Location address not set'
        self.memory[self.location_addr] = value

    def input(self):
        self.send(input('cpu> '))

    def send(self, cmd):
        self.input_buffer = list(cmd + '\n')
        self.run()

    def interactive(self):
        self.is_interactive = True
        try:
            while True:
                self.run()
                print(self.read(), end='')
                self.input()
        except EOFError:
            pass
        finally:
            self.is_interactive = False

    def read(self):
        '''Read and remove all data from the output buffer'''

        result = self.output_buffer
        self.output_buffer = ''
        return result

    def run(self):
        '''Run until halted or more keyboard input is needed'''

        while self.step():
            pass

    def get_next_instruction(self):
        return read_instruction(self.memory, self.pc)

    def step(self):
        ''' Returns False if halted or waiting for input '''

        opcode, args = self.get_next_instruction()
        self.ticks += 1
        return self.execute(opcode, args)

    def set_reg(self, arg: int, value: int):
        self.registers[to_reg(arg)] = value

    def execute(self, opcode, args):
        '''
        Executes the given instruction, updates the program counter, and
        returns False if halted or waiting for input
        '''

        new_pc = self.pc + len(opcode)
        a, b, c = args + (None, ) * (3 - len(args))

        match opcode.name:
            case 'noop':
                pass

            case 'halt':
                return False

            case 'out':
                self.output_buffer += chr(self.value(a))

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
                if not self.input_buffer:
                    return False

                self.set_reg(a, ord(self.input_buffer.pop(0)))

            case _:
                raise NotImplementedError(
                    f'Not implemented: {opcode=} {args=}'
                )

        self.pc = new_pc
        return True

    def snapshot(self):
        return {
            k: copy.deepcopy(getattr(self, k))
            for k in self.SNAPSHOT_ATTRS
        }

    def clone(self):
        return self.__class__.from_snapshot(self.snapshot())

    def load_snapshot(self, state: dict[str, Any]):
        for attrib in self.SNAPSHOT_ATTRS:
            setattr(self, attrib, copy.deepcopy(state[attrib]))

    @override
    def __repr__(self):
        return f'<{self.__class__.__name__}(pc={self.pc}, loc={self.location})>'

    @staticmethod
    def read_snapshot_file(fname):
        with open(fname) as f:
            return ast.literal_eval(f.read())

    @classmethod
    def from_snapshot_file(cls, fname):
        return cls.from_snapshot(cls.read_snapshot_file(fname))

    @classmethod
    def from_snapshot(cls, snapshot):
        vm = cls()
        vm.load_snapshot(snapshot)
        return vm
