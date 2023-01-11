#!/usr/bin/env python3
from cpu import CPU
from utils import read_instruction, isreg

def format_instruction(opcode, args):
    # allows multi-character output format
    if opcode.name == 'out' and isinstance(args[0], str):
        return opcode.name + ' ' + repr(args[0])

    argregs = [f'r{v-32768}' if v >= 32768 else v for v in args]
    if opcode.name == 'out' and isinstance(argregs[0], int):
        argregs = repr(chr(args[0]))
    elif not args:
        argregs = ''
    else:
        argregs = ' '.join(map(str, argregs))

    return opcode.name + ' ' + argregs

def disassemble(memory: list[int], addr=0):
    while addr < len(memory):
        try:
            opcode, args = read_instruction(memory, addr)
            curaddr = addr

            # combine multiple character outputs into one string
            if opcode.name == 'out' and not isreg(args[0]):
                outstring = chr(args[0])
                next_addr = addr + len(opcode)
                while True:
                    next_opcode, next_args = read_instruction(memory, next_addr)
                    if next_opcode.name != 'out' or isreg(next_args[0]):
                        break

                    outstring += chr(next_args[0])
                    addr = next_addr
                    next_addr += len(opcode)
                args = (outstring,)

            print(curaddr, format_instruction(opcode, args))
            addr += len(opcode)

        except KeyError:
            print(addr, 'err [%s]' % memory[addr])
            addr += 1

def main():
    # vm = CPU('challenge.bin')
    vm = CPU.from_snapshot_file('snapshots/start')
    disassemble(vm.memory, 0)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
