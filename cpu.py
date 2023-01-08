import re
import readline
import sys
from dataclasses import dataclass


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

def debug(*args, **kwargs):
    if '-d' in sys.argv:
        print(*args, **kwargs)

def isreg(arg):
    return arg >= 32768

def to_register(arg):
    if isreg(arg):
        return arg - 32768
    return arg

class CPU:
    def __init__(self):
        self.memory = None
        self.registers = [0] * 8
        self.stack = []
        self.pc = 0  # program counter
        self.input_buffer = []  # keyboard input
        self.halted = False

    def readvalue(self, arg):
        if isreg(arg):
            return self.registers[arg - 32768]
        return arg

    def read_instruction(self, bytecode, addr):
        opid = bytecode[addr]
        opcode = OPCODES[opid]
        args = tuple(bytecode[addr+1:addr+1+opcode.nargs])
        return opcode, args

    def run(self, fname='challenge.bin'):
        self.memory = load_bytecode(fname)
        self.pc = 0
        while not self.halted:
            self.step()

    def step(self):
        opcode, args = self.read_instruction(self.memory, self.pc)
        nextpc = self.pc + len(opcode)
        a, b, c = args + (None,) * (3 - len(args))
        debug(self.pc, opcode.name, args)

        match opcode.name:
            case 'noop':
                pass

            case 'halt':
                self.halted = True
                return

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
                    self.halted = True
                    return
                nextpc = self.stack.pop()

            # read a character from the terminal and write its ascii code to <a>; it can
            # be assumed that once input starts, it will continue until a newline is
            # encountered; this means that you can safely read whole lines from the
            # keyboard and trust that they will be fully read
            case 'in':
                # TODO: add hook/event
                a = to_register(a)
                if not self.input_buffer:
                    self.input_buffer = list(input('> ') + '\n')[::-1]
                self.registers[a] = ord(self.input_buffer.pop())

            case _:
                print('unimplemented:', opcode, args)
                self.halted = True
                return

        self.pc = nextpc
