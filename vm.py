#!/usr/bin/env python3
import readline
import sys
from colorama import Fore, Style
from specs import OPCODES, WORD_BYTES, load_bytecode


def debug(*args, **kwargs):
    if '-d' in sys.argv:
        print(*args, **kwargs)

def isreg(arg):
    return arg >= 32768

class CPU:
    def __init__(self):
        self.memory = {}
        self.registers = [0] * 8
        self.stack = []
        self.input_buffer = []

    def readvalue(self, arg):
        if isreg(arg):
            return self.registers[arg - 32768]
        return arg

    def val_to_reg(self, arg):
        if isreg(arg):
            return arg - 32768
        return arg

    def read_instruction(self, bytecode, addr):
        opid = bytecode[addr]
        opcode = OPCODES[opid]
        args = tuple(bytecode[addr+1:addr+1+opcode.nargs])
        return opcode, args, addr + len(opcode)

    def run_program(self, fname):

        bytecode = load_bytecode('challenge.bin')

        pc = 0
        while True:
            opcode, args, nextpc = self.read_instruction(bytecode, pc)
            debug(pc, opcode.name, args)
            a, b, c = args + (None,) * (3 - len(args))

            match opcode.name:
                case 'noop':
                    pass

                case 'halt':
                    break

                case 'out':
                    a = self.readvalue(a)
                    print(chr(a), end='')

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
                    a = self.val_to_reg(a)
                    b = self.readvalue(b)
                    self.registers[a] = b

                case 'add':
                    a = self.val_to_reg(a)
                    b = self.readvalue(b)
                    c = self.readvalue(c)
                    self.registers[a] = (b + c) % 32768

                case 'eq':
                    a = self.val_to_reg(a)
                    b = self.readvalue(b)
                    c = self.readvalue(c)
                    self.registers[a] = int(b == c)

                case 'push':
                    a = self.readvalue(a)
                    self.stack.append(a)

                case 'pop':
                    a = self.val_to_reg(a)
                    self.registers[a] = self.stack.pop()

                case 'gt':
                    a = self.val_to_reg(a)
                    b = self.readvalue(b)
                    c = self.readvalue(c)
                    self.registers[a] = int(b > c)

                case 'and':
                    a = self.val_to_reg(a)
                    b = self.readvalue(b)
                    c = self.readvalue(c)
                    self.registers[a] = int(b & c)

                case 'or':
                    a = self.val_to_reg(a)
                    b = self.readvalue(b)
                    c = self.readvalue(c)
                    self.registers[a] = int(b | c)

                case 'not':
                    a = self.val_to_reg(a)
                    b = self.readvalue(b)
                    self.registers[a] = ~b & (2**15-1)

                case 'call':
                    self.stack.append(nextpc)
                    nextpc = self.readvalue(a)

                case 'mult':
                    a = self.val_to_reg(a)
                    b = self.readvalue(b)
                    c = self.readvalue(c)
                    self.registers[a] = (b * c) % 32768

                case 'mod':
                    a = self.val_to_reg(a)
                    b = self.readvalue(b)
                    c = self.readvalue(c)
                    self.registers[a] = (b % c)

                # read memory at address <b> and write it to <a>
                case 'rmem':
                    a = self.val_to_reg(a)
                    b = self.readvalue(b)
                    self.registers[a] = bytecode[b]

                # write the value from <b> into memory at address <a>
                case 'wmem':
                    a = self.readvalue(a)
                    b = self.readvalue(b)
                    bytecode[a] = b

                # remove the top element from the stack and jump to it; empty stack = halt
                case 'ret':
                    if not self.stack:
                        break
                    nextpc = self.stack.pop()

                # read a character from the terminal and write its ascii code to <a>; it can
                # be assumed that once input starts, it will continue until a newline is
                # encountered; this means that you can safely read whole lines from the
                # keyboard and trust that they will be fully read
                case 'in':
                    a = self.val_to_reg(a)
                    if not self.input_buffer:
                        cmd = list(input('> ') + '\n')[::-1]
                        if not cmd:
                            print('Invalid')
                            continue
                        self.input_buffer = cmd
                    self.registers[a] = ord(self.input_buffer.pop())

                case _:
                    print('unimplemented:', opcode, args)
                    break

            pc = nextpc


def main():
    cpu = CPU()
    cpu.run_program('challenge.bin')

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        pass
