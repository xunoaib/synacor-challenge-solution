#!/usr/bin/env python3
import argparse
import string
import sys

from vm import VM


def dump_text_section():
    vm = VM.from_snapshot_file('snapshots/start')

    s = ''
    start_idx = 6072
    for i, v in enumerate(vm.memory[start_idx:], start=start_idx):
        ch = chr(v)
        if ch not in string.printable:
            ch = '\n\n'
        s += ch
    print(f'\033[92m{start_idx}:\033[0m {repr(s)}')


def dump_text_section_addrs():
    vm = VM.from_snapshot_file('snapshots/start')

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
    parser.add_argument('-f', '--file', default='challenge.bin')
    args = parser.parse_args()

    print('Loading binary:', args.file)

    vm = VM(args.file)
    # vm = EnhancedCPU.from_snapshot_file('snapshots/start')

    print(vm.read())
    if args.commands:
        for cmd in args.commands.split(';'):
            vm.send(cmd.strip())
            print(vm.read())
    vm.interactive()


if __name__ == '__main__':
    try:
        if '-dt' in sys.argv:
            dump_text_section()
        else:
            main()
    except (KeyboardInterrupt, EOFError, BrokenPipeError):
        pass
