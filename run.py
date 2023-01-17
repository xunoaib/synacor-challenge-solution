#!/usr/bin/env python3
import string
import argparse

from enhancedcpu import EnhancedCPU

def dump_text_section():
    vm = EnhancedCPU.from_snapshot_file('snapshots/start')

    s = ''
    for v in vm.memory[6072:]:
        ch = chr(v)
        if ch not in string.printable:
            ch = '\n\n'
        s += ch
    print(s)

def dump_text_section_addrs():
    vm = EnhancedCPU.from_snapshot_file('snapshots/start')

    addr = 6072
    buffer = ''
    for v in vm.memory[addr:]:
        if v < 256:
            if not buffer:
                print(f'>>>{addr}<<<', end=' ')
            print(chr(v), end='')
            buffer += chr(v)
        else:
            if buffer:
                print(buffer)
                buffer = ''
            print(f'>>>{addr}<<<', v)
        addr += 1

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--commands')
    args = parser.parse_args()

    # vm = enhancedcpu('challenge.bin')
    # vm = EnhancedCPU.from_snapshot_file('snapshots/start')
    # vm.debug_cmd('giveall')
    # vm.debug_cmd('load coins')
    vm = EnhancedCPU.from_snapshot_file('snapshots/teleported')

    print(vm.read())
    if args.commands:
        for cmd in args.commands.split(';'):
            vm.send(cmd.strip())
            print(vm.read())
    vm.interactive()

if __name__ == '__main__':
    try:
        main()
        # dump_text_section()
    except (KeyboardInterrupt, EOFError, BrokenPipeError):
        pass
