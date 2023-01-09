import ast
import os
import re
import readline
import sys
from dataclasses import dataclass

from debugger import exec_debug_cmd

@dataclass
class Opcode:
    name: str
    id: int
    nargs: int

    def __len__(self):
        return 1 + self.nargs

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

def load_bytecode(fname):
    with open(fname, 'rb') as f:
        data = f.read()

    return [
        int.from_bytes(data[i:i+2], 'little')
        for i in range(0, len(data), 2)
    ]

def isreg(arg):
    return arg >= 32768

def to_register(arg):
    if isreg(arg):
        return arg - 32768
    return arg

# def print_debug(*args, **kwargs):
#     # if '-d' in sys.argv:
#         print(*args, **kwargs)

def read_instruction(memory, addr):
    opid = memory[addr]
    opcode = OPCODES[opid]
    args = tuple(memory[addr+1:addr+1+opcode.nargs])
    return opcode, args


class CPU:
    def __init__(self):
        self.memory = []
        self.registers = [0] * 8
        self.stack = []
        self.pc = 0  # program counter
        self.input_buffer = []  # keyboard input

    def load_program(self, fname):
        self.memory = load_bytecode(fname)
        self.pc = 0

    def readvalue(self, arg):
        if isreg(arg):
            return self.registers[arg - 32768]
        return arg

    def run(self):
        while self.step():
            pass

    def step(self):
        opcode, args = read_instruction(self.memory, self.pc)
        # self.print_debug(self.pc, opcode.name, args)
        return self.execute(opcode, args)

    def execute(self, opcode, args):
        '''
        Executes the given instruction, updates the program counter, and
        returns true if the program has not halted.
        '''
        nextpc = self.pc + len(opcode)
        a, b, c = args + (None,) * (3 - len(args))

        match opcode.name:
            case 'noop':
                pass

            case 'halt':
                return False

            case 'out':
                a = self.readvalue(a)
                print(chr(a), end='', flush=True)

            case 'jmp':
                nextpc = a

            case 'jt':
                a = self.readvalue(a)
                if a != 0:
                    nextpc = b

            case 'jf':
                a = self.readvalue(a)
                if a == 0:
                    nextpc = b

            case 'set':
                a = to_register(a)
                b = self.readvalue(b)
                self.registers[a] = b

            case 'add':
                a = to_register(a)
                b = self.readvalue(b)
                c = self.readvalue(c)
                self.registers[a] = (b + c) % 32768

            case 'eq':
                a = to_register(a)
                b = self.readvalue(b)
                c = self.readvalue(c)
                self.registers[a] = int(b == c)

            case 'push':
                a = self.readvalue(a)
                self.stack.append(a)

            case 'pop':
                a = to_register(a)
                self.registers[a] = self.stack.pop()

            case 'gt':
                a = to_register(a)
                b = self.readvalue(b)
                c = self.readvalue(c)
                self.registers[a] = int(b > c)

            case 'and':
                a = to_register(a)
                b = self.readvalue(b)
                c = self.readvalue(c)
                self.registers[a] = int(b & c)

            case 'or':
                a = to_register(a)
                b = self.readvalue(b)
                c = self.readvalue(c)
                self.registers[a] = int(b | c)

            case 'not':
                a = to_register(a)
                b = self.readvalue(b)
                self.registers[a] = ~b & (2**15-1)

            case 'call':
                self.stack.append(nextpc)
                nextpc = self.readvalue(a)

            case 'mult':
                a = to_register(a)
                b = self.readvalue(b)
                c = self.readvalue(c)
                self.registers[a] = (b * c) % 32768

            case 'mod':
                a = to_register(a)
                b = self.readvalue(b)
                c = self.readvalue(c)
                self.registers[a] = (b % c)

            # read memory at address <b> and write it to <a>
            case 'rmem':
                a = to_register(a)
                b = self.readvalue(b)
                self.registers[a] = self.memory[b]

            # write the value from <b> into memory at address <a>
            case 'wmem':
                a = self.readvalue(a)
                b = self.readvalue(b)
                self.memory[a] = b

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
                a = to_register(a)
                if not self.input_buffer:
                    cmd = input('> ')
                    # intercept special debug commands
                    if cmd.startswith('!'):
                        exec_debug_cmd(self, cmd[1:])
                        return True
                    self.input_buffer = list(cmd + '\n')[::-1]
                self.registers[a] = ord(self.input_buffer.pop())

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
        }

    def restore_snapshot(self, snapshot: dict):
        for attrib in ['memory', 'stack', 'registers', 'pc', 'input_buffer']:
            setattr(self, attrib, snapshot[attrib])

    def __repr__(self):
        return '\n'.join([
            f'memory = {self.memory}',
            f'stack = {self.memory}',
            f'registers = {self.registers}',
            f'pc = {self.pc}',
        ])
