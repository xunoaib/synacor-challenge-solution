#!/usr/bin/env python3

from cpu import CPU
# from debugger import Debugger

def main():
    vm = CPU()
    vm.load_program('challenge.bin')
    vm.run()

    # debug(cpu)
    # Debugger(cpu).run('challenge.bin')

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        pass
