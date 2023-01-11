#!/usr/bin/env python3
import string

from debugger import Debugger

def dump_text_section():
    vm = Debugger.from_snapshot_file('snapshots/start')

    s = ''
    for v in vm.memory[6072:]:
        ch = chr(v)
        if ch not in string.printable:
            ch = '\n'
        s += ch
    print(s)

def dump_text_section_addrs():
    vm = Debugger.from_snapshot_file('snapshots/start')

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
    # vm = Debugger('snapshots/coins')
    vm = Debugger.from_snapshot_file('snapshots/start')
    # vm.debug_cmd('giveall')
    # vm.debug_cmd('load coins')

    # vm.run()
    # vm.process_input('look')

    while True:
        vm.run()
        print(vm.read(), end='')
        vm.input()


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        pass
