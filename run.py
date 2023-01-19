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

def brute_call_6027():
    vm = EnhancedCPU.from_snapshot_file('snapshots/teleported')
    vm.read()
    snapshot = vm.snapshot()

    import sys

    messages = {}
    for r in range(353,32768):
        print(r, file=sys.stderr, end=' ', flush=True)

        vm = EnhancedCPU.from_snapshot(snapshot)
        vm.registers[7] = r
        vm.send('use teleporter')
        message = vm.read().strip()
        if message not in messages:
            print(f'\n>>> {r=}\n', flush=True)
            print(message, flush=True)
            messages[message] = r

def debug_call_6027():
    vm = EnhancedCPU.from_snapshot_file('snapshots/teleported')

    # extract 6027 function as bytes and dump to file
    with open('call_6027.bin', 'wb') as f:
        start, end = 6027, 6068

        # set initial r0, r1, r7
        values = [
            1, 32768 + 0, 1,  # r0 = 1
            1, 32768 + 1, 2,  # r1 = 2
            1, 32768 + 7, 8,  # r7 = 8
            17, 6027,         # call 6027
            0                 # halt
        ]

        startaddr = start - len(values)

        # pad the file with noops to preserve jump target addresses
        values = [21] * startaddr + values

        for value in values + vm.memory[start:end]:
            f.write(int.to_bytes(value, 2, 'little'))

    vm = EnhancedCPU('call_6027.bin')
    vm.pc = startaddr
    vm.run()

if __name__ == '__main__':
    try:
        # brute_call_6027()
        main()
        # debug_call_6027()
        # dump_text_section()
    except (KeyboardInterrupt, EOFError, BrokenPipeError):
        pass
