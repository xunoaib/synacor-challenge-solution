#!/usr/bin/env python3
from cpu import CPU, read_instruction

def disassemble(memory: list[int], addr=0):
    while addr < len(memory):
        try:
            opcode, args = read_instruction(memory, addr)
            if not args:
                args = ''
            if opcode.name == 'out':
                args = repr(chr(args[0]))
            print(hex(addr), opcode.name, args)
            addr += len(opcode)
        except KeyError:
            print(hex(addr), 'invalid', memory[addr])
            addr += 1

def main():
    vm = CPU()
    vm.load_program('challenge.bin')
    disassemble(vm.memory, vm.pc)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
