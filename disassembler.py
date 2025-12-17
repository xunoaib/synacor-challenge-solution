import argparse
import string

from utils import isreg, read_instruction


def format_instruction_plain(opcode, args):
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


def format_instruction_sensible(opcode, args):
    # allows multi-character output format
    if opcode.name == 'out' and isinstance(args[0], str):
        return opcode.name + ' ' + repr(args[0])

    argregs = [f'r{v-32768}' if v >= 32768 else v for v in args]
    if opcode.name == 'out' and isinstance(argregs[0], int):
        argregs = repr(chr(args[0]))
    elif not args:
        argregs = ''
    else:
        argregs = list(map(str, argregs))
        mathsyms = {'and': '&', 'or': '|', 'mult': '*', 'mod': '%', 'add': '+'}
        match opcode.name:
            case 'and' | 'or' | 'mult' | 'mod' | 'add':
                return '{0} = {1} {3} {2}'.format(
                    *argregs, mathsyms[opcode.name]
                )
            case 'set':
                return '{} = {}'.format(*argregs)
            case 'not':
                return '{} = ~{}'.format(*argregs)
            case 'gt':
                return '{} = {} > {}'.format(*argregs)
            case 'jt':
                return 'jmp {} if {} > 0'.format(*argregs[::-1])
            case 'jf':
                return 'jmp {} if {} = 0'.format(*argregs[::-1])
            case 'eq':
                return '{} = ({} == {})'.format(*argregs)
            case 'rmem':
                return '{} = mem[{}]'.format(*argregs)
            case 'wmem':
                return 'mem[{}] = {}'.format(*argregs)
        argregs = ' '.join(map(str, argregs))
    return opcode.name + ' ' + argregs


format_instruction = format_instruction_sensible
format_instruction = format_instruction_plain


def disassemble(memory: list[int], addr=0, lines=15):
    while addr < len(memory) and lines > 0:
        try:
            opcode, args = read_instruction(memory, addr)
            curaddr = addr

            # combine multiple character outputs into one string
            if opcode.name == 'out' and not isreg(args[0]):
                outstring = chr(args[0])
                next_addr = addr + len(opcode)
                while True:
                    next_opcode, next_args = read_instruction(
                        memory, next_addr
                    )
                    if next_opcode.name != 'out' or isreg(next_args[0]):
                        break

                    outstring += chr(next_args[0])
                    addr = next_addr
                    next_addr += len(opcode)
                args = (outstring, )

            print(curaddr, '', format_instruction(opcode, args))
            addr += len(opcode)
            lines -= 1

        except KeyError:
            val = memory[addr]
            if val < 256 and chr(val) in string.printable:
                val = repr(chr(val)) + f' [{val}]'
            else:
                val = f'[{val}]'
            print(addr, ' err %s' % val)
            addr += 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', default='challenge.bin')
    args = parser.parse_args()

    from cpu import CPU
    vm = CPU(args.file)
    disassemble(vm.memory, 0, len(vm.memory))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
