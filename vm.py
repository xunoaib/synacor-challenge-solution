#!/usr/bin/env python3
from specs import OPCODES, WORD_BYTES


class CPU:
    def __init__(self):
        self.memory = {}
        self.registers = [0] * 8
        self.stack = {}

    def run_program(self, fname):
        with open(fname, 'rb') as f:
            bytecode = f.read()

        pc = 0
        while True:
            opcode, args, pc = self.read_instruction(bytecode, pc)
            match opcode.name:
                case 'out':
                    print(chr(args[0]), end='')
                case 'halt':
                    break

    def read_instruction(self, bytecode, addr):
        opid = bytecode[addr]
        opcode = OPCODES[opid]
        args = tuple(
            int.from_bytes(bytecode[i:i+WORD_BYTES], 'little')
            for i in range(addr+WORD_BYTES, addr+1+opcode.nargs*WORD_BYTES, WORD_BYTES)
        )
        next_addr = addr + WORD_BYTES + opcode.nargs * WORD_BYTES
        return opcode, args, next_addr


def main():
    cpu = CPU()
    cpu.run_program('challenge.bin')

if __name__ == '__main__':
    main()
