import re
from dataclasses import dataclass

WORD_BYTES = 2

@dataclass
class Opcode:
    name: str
    id: int
    nargs: int

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
