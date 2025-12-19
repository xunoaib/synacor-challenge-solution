import ast
import copy
from typing import override

from utils import (calculate_location_addr, isreg, load_bytecode,
                   read_instruction, to_register)


class BaseVM:

    def __init__(self, fname=None):
        self.memory = []
        self.registers = [0] * 8
        self.stack = []
        self.pc = 0  # program counter
        self.input_buffer = []  # keyboard input buffer
        self.output_buffer = ''
        self.ticks = 0
        self.location_addr: int | None = None

        if fname:
            self.load_program(fname)

    def load_program(self, fname):
        self.memory = load_bytecode(fname)
        self.pc = 0
        print('Calculating location address')
        self.location_addr = calculate_location_addr(self)

    def readvalue(self, arg):
        return self.registers[arg - 32768] if isreg(arg) else arg

    def set_register(self, regidx, val):
        self.registers[regidx] = val

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

    def flush(self):
        self.read()
        return self

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
                self.output_buffer += chr(self.readvalue(a))

            case 'jmp':
                nextpc = a

            case 'jt':
                if self.readvalue(a) != 0:
                    nextpc = b

            case 'jf':
                if self.readvalue(a) == 0:
                    nextpc = b

            case 'set':
                self.set_register(
                    to_register(a),
                    self.readvalue(b),
                )

            case 'add':
                self.set_register(
                    to_register(a),
                    (self.readvalue(b) + self.readvalue(c)) % 32768
                )

            case 'eq':
                self.set_register(
                    to_register(a),
                    int(self.readvalue(b) == self.readvalue(c))
                )

            case 'push':
                self.stack.append(self.readvalue(a))

            case 'pop':
                self.set_register(to_register(a), self.stack.pop())

            case 'gt':
                self.set_register(
                    to_register(a),
                    int(self.readvalue(b) > self.readvalue(c)),
                )

            case 'and':
                self.set_register(
                    to_register(a),
                    int(self.readvalue(b) & self.readvalue(c)),
                )

            case 'or':
                self.set_register(
                    to_register(a),
                    int(self.readvalue(b) | self.readvalue(c)),
                )

            case 'not':
                self.set_register(
                    to_register(a),
                    ~self.readvalue(b) & (2**15 - 1),
                )

            case 'call':
                self.stack.append(nextpc)
                nextpc = self.readvalue(a)

            case 'mult':
                self.set_register(
                    to_register(a),
                    (self.readvalue(b) * self.readvalue(c)) % 32768
                )

            case 'mod':
                self.set_register(
                    to_register(a),
                    (self.readvalue(b) % self.readvalue(c)),
                )

            # read memory at address <b> and write it to <a>
            case 'rmem':
                self.set_register(
                    to_register(a),
                    self.memory[self.readvalue(b)],
                )

            # write the value from <b> into memory at address <a>
            case 'wmem':
                self.memory[self.readvalue(a)] = self.readvalue(b)

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

                self.set_register(
                    to_register(a),
                    ord(self.input_buffer.pop(0)),
                )

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
