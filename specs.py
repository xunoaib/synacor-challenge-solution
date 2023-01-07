import re
from dataclasses import dataclass

WORD_BYTES = 2

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
        int.from_bytes(data[i:i+WORD_BYTES], 'little')
        for i in range(0, len(data), WORD_BYTES)
    ]

def parse_opcodes():
    with open('arch-spec') as f:
        data = f.read()

    opcodes = {}
    for name, opid, args in re.findall(r'(.*): (\d+)(.*?)\n', data):
        nargs = len(args.strip().split())
        opid = int(opid)
        opcodes[opid] = Opcode(name, opid, nargs)
    return opcodes

OPCODES = parse_opcodes()
