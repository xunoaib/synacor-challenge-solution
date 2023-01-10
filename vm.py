#!/usr/bin/env python3
import string

from cpu import CPU
from disassembler import disassemble
from debugger import debug_cmd

def main():
    vm = CPU()

    # vm.load_program('challenge.bin')

    snapshot = CPU.read_snapshot('snapshots/start')
    vm.restore_snapshot(snapshot)

    # debug_cmd(vm, 'giveall')
    # debug_cmd(vm, 'load coins')

    vm.run()
    return

    # # dump text section to a binary file
    # with open('text.section', 'wb') as f:
    #     addr = 6072
    #     buffer = ''
    #     for v in vm.memory[addr:]:
    #         if v < 256:
    #             if not buffer:
    #                 print(f'>>>{addr}<<<', end=' ')
    #             print(chr(v), end='')
    #             buffer += chr(v)
    #         else:
    #             if buffer:
    #                 print(buffer)
    #                 buffer = ''
    #             print(f'>>>{addr}<<<', v)
    #         addr += 1
    #     # addr = 6072
    #     # while addr < len(vm.memory):
    #         # f.write(int.to_bytes(v, 2, 'little'))
    # return

    # print text section
    s = ''
    for v in vm.memory[6072:]:
        ch = chr(v)
        if ch not in string.printable:
            ch = '\n'
        s += ch
    print(s)

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        pass
