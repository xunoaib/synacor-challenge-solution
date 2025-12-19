import re
from dataclasses import dataclass


@dataclass
class Opcode:
    name: str
    id: int
    nargs: int

    def __len__(self):
        return 1 + self.nargs


def load_bytecode(fname):
    with open(fname, 'rb') as f:
        data = f.read()

    return [
        int.from_bytes(data[i:i + 2], 'little')
        for i in range(0, len(data), 2)
    ]


def is_reg(arg: int):
    return arg >= 32768


def to_reg(arg: int):
    return arg - 32768 if is_reg(arg) else arg


def read_instruction(memory: list[int], addr: int):
    opid = memory[addr]
    opcode = OPCODES[opid]
    args = tuple(memory[addr + 1:addr + 1 + opcode.nargs])
    return opcode, args


def parse_opcodes(arch_spec_fname='arch-spec') -> dict[int, Opcode]:
    with open(arch_spec_fname) as f:
        data = f.read()

    opcodes = {}
    for name, opid, args in re.findall(r'(.*): (\d+)(.*?)\n', data):
        nargs = len(args.strip().split())
        opid = int(opid)
        opcodes[opid] = Opcode(name, opid, nargs)
    return opcodes


OPCODES = parse_opcodes()
