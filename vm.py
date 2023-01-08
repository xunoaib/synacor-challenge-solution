#!/usr/bin/env python3

from cpu import CPU

def main():
    cpu = CPU()
    cpu.run('challenge.bin')

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        pass
