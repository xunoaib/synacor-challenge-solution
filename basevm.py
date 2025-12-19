import ast
import copy
from typing import override

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

    def __init__(self, binfile=None):
        self.memory = []
        self.registers = Registers()
        self.stack = []
        self.pc = 0  # program counter
        self.input_buffer = []  # keyboard input buffer
        self.output_buffer = ''
        self.ticks = 0
        self.location_addr: int | None = None

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
        try:
            while True:
                self.run()
                print(self.read(), end='')
                self.input()
        except EOFError:
            pass

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
        opcode, args = self.get_next_instruction()
        self.ticks += 1
        return self.execute(opcode, args)

    def execute(self, opcode, args):
        '''
        Executes the given instruction, updates the program counter, and
        returns true if the program has not halted.
        '''
        nextpc = self.pc + len(opcode)
        a, b, c = args + (None, ) * (3 - len(args))

        match opcode.name:
            case 'noop':
                pass

            case 'halt':
                return False

            case 'out':
                self.output_buffer += chr(self.value(a))

            case 'jmp':
                nextpc = a

            case 'jt':
                if self.value(a) != 0:
                    nextpc = b

            case 'jf':
                if self.value(a) == 0:
                    nextpc = b

            case 'set':
                self.registers[to_reg(a)] = self.value(b)

            case 'add':
                v = (self.value(b) + self.value(c)) % 32768
                self.registers[to_reg(a)] = v

            case 'eq':
                v = int(self.value(b) == self.value(c))
                self.registers[to_reg(a)] = v

            case 'push':
                self.stack.append(self.value(a))

            case 'pop':
                self.registers[to_reg(a)] = self.stack.pop()

            case 'gt':
                v = int(self.value(b) > self.value(c))
                self.registers[to_reg(a)] = v

            case 'and':
                v = int(self.value(b) & self.value(c))
                self.registers[to_reg(a)] = v

            case 'or':
                v = int(self.value(b) | self.value(c))
                self.registers[to_reg(a)] = v

            case 'not':
                v = ~self.value(b) & (2**15 - 1)
                self.registers[to_reg(a)] = v

            case 'call':
                self.stack.append(nextpc)
                nextpc = self.value(a)

            case 'mult':
                v = (self.value(b) * self.value(c)) % 32768
                self.registers[to_reg(a)] = v

            case 'mod':
                v = self.value(b) % self.value(c)
                self.registers[to_reg(a)] = v

            # read memory at address <b> and write it to <a>
            case 'rmem':
                self.registers[to_reg(a)] = self.memory[self.value(b)]

            # write the value from <b> into memory at address <a>
            case 'wmem':
                self.memory[self.value(a)] = self.value(b)

            # remove the top element from the stack and jump to it; empty stack = halt
            case 'ret':
                if not self.stack:
                    return False
                nextpc = self.stack.pop()

            # read a character from the terminal and write its ascii code to <a>; it can
            # be assumed that once input starts, it will continue until a newline is
            # encountered; this means that you can safely read whole lines from the
            # keyboard and trust that they will be fully read
            case 'in':
                # pause program when input buffer is empty
                if not self.input_buffer:
                    return False

                self.registers[to_reg(a)] = ord(self.input_buffer.pop(0))

            case _:
                print('unimplemented:', opcode, args)
                return False

        self.pc = nextpc
        return True

    def snapshot(self):
        return {
            'memory': self.memory,
            'stack': self.stack,
            'registers': self.registers,
            'pc': self.pc,
            'input_buffer': self.input_buffer,
            'output_buffer': self.output_buffer,
            'location_addr': self.location_addr,
        }

    def clone(self):
        snapshot = self.snapshot()
        return self.__class__.from_snapshot(snapshot)

    def load_snapshot(self, snapshot: dict):
        for attrib in [
            'memory', 'stack', 'registers', 'pc', 'input_buffer',
            'output_buffer', 'location_addr'
        ]:
            setattr(self, attrib, copy.deepcopy(snapshot[attrib]))

    @override
    def __repr__(self):
        return f'<{self.__class__.__name__}(pc={self.pc}, loc={self.location})>'

    @staticmethod
    def read_snapshot(fname):
        with open(fname) as f:
            return ast.literal_eval(f.read())

    @classmethod
    def from_snapshot_file(cls, fname):
        snapshot = cls.read_snapshot(fname)
        return cls.from_snapshot(snapshot)

    @classmethod
    def from_snapshot(cls, snapshot):
        vm = cls()
        vm.load_snapshot(snapshot)
        return vm
