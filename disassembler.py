import argparse
import string
from dataclasses import dataclass
from typing import override

from utils import Opcode, is_reg, read_instruction


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
# format_instruction = format_instruction_plain


@dataclass
class Instruction:
    address: int
    opcode: Opcode
    args: tuple[int, ...]


@dataclass
class Instructions:
    instructions: list[Instruction]

    @override
    def __repr__(self) -> str:
        inst = self.instructions[0]
        if inst.opcode.name == 'out':
            assert all(i.opcode.name == 'out' for i in self.instructions)
            args = (''.join(chr(i.args[0]) for i in self.instructions), )
        else:
            args = inst.args

        return f'{inst.address:>5}  {format_instruction(inst.opcode, args)}'


@dataclass
class RawValue:
    address: int
    values: list[int]

    def is_ascii(self):
        return all(v < 256 and chr(v) in string.printable for v in self.values)

    def ascii(self):
        return ''.join(map(chr, self.values))

    @override
    def __repr__(self) -> str:
        if self.is_ascii():
            return f'{self.address:>5}  ascii {self.ascii()!r}'
        else:
            assert len(self.values) == 1
            return f'{self.address:>5}  byte [{self.values[0]}]'


def disassemble(memory: list[int], addr=0, lines=15):
    results = []
    instructions = []

    while addr < len(memory) and lines > 0:
        try:
            opcode, args = read_instruction(memory, addr)
            curaddr = addr
            instructions.append(Instruction(curaddr, opcode, args))

            # combine multiple character outputs into one string
            if opcode.name == 'out' and not is_reg(args[0]):
                outstring = chr(args[0])
                next_addr = addr + len(opcode)
                while True:
                    next_opcode, next_args = read_instruction(
                        memory, next_addr
                    )
                    if next_opcode.name != 'out' or is_reg(next_args[0]):
                        break
                    instructions.append(
                        Instruction(curaddr, next_opcode, next_args)
                    )
                    outstring += chr(next_args[0])
                    addr = next_addr
                    next_addr += len(opcode)
                args = (outstring, )

            # print(curaddr, '', format_instruction(opcode, args))
            addr += len(opcode)
            lines -= 1

            results.append(Instructions(instructions))
            instructions = []

        except KeyError:
            val = memory[addr]
            rv = RawValue(addr, [val])

            # # merge contiguous ascii characters into one.
            # # NOTE: some ascii will be misinterpreted as other instructions
            # if rv.is_ascii() and results:
            #     top = results[-1]
            #     if isinstance(top, RawValue) and top.is_ascii():
            #         rv = RawValue(top.address, top.values + rv.values)
            #         results.pop()

            results.append(rv)
            addr += 1

    for r in results:
        print(r)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', default='challenge.bin')
    args = parser.parse_args()

    from vm import VM
    vm = VM(args.file)

    # # before decryption
    # disassemble(vm.memory, 0, len(vm.memory))

    # after decryption
    vm.run()
    disassemble(vm.memory, 0, len(vm.memory))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
