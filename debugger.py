import ast
from pathlib import Path
from itertools import zip_longest

# TODO:
# - wrap CPU.execute() to add pre/post hooks and callback conditions
# - breakpoint on: address, instruction

class Debugger:
    def __init__(self, cpu):
        self.cpu = cpu

def diff_snapshot(snap1, snap2):
    diff_result = {}
    for key in snap1:
        v1 = snap1[key]
        v2 = snap2[key]

        if v1 == v2:
            continue

        if isinstance(v1, list):
            diff_result[key] = [(idx, subv1, subv2) for idx, (subv1, subv2) in
                                enumerate(zip_longest(v1, v2)) if subv1 != subv2]
        else:
            diff_result[key] = (v1, v2)
    return diff_result

def debug_cmd(cpu, cmd):
    directory = Path('snapshots')
    try:
        match cmd.split():
            case ['dump']:
                print(repr(cpu))

            case ['dump', fname]:
                if Path(fname).exists():
                    if input(f'{fname} already exists. Overwrite? [y/N] ') != 'y':
                        return
                with open(fname, 'w') as f:
                    f.write(repr(cpu))
                print('saved to', fname)

            # case ['debug', ('on' | 'off') as val]:
            #     cpu.debug = val == 'on'
            #     print(f'set debug = {cpu.debug}')

            case ['save', *fname]:
                if not fname:
                    fname = ['last']
                directory.mkdir(exist_ok=True)
                fname = directory / fname[0]
                with open(fname, 'w') as f:
                    f.write(str(cpu.snapshot()))
                print('saved snapshot to', fname)

            case ['load', fname]:
                print(f'restoring snapshot "{fname}"')
                with open(directory / fname) as f:
                    snapshot = ast.literal_eval(f.read())
                cpu.restore_snapshot(snapshot)

            case ['diff', fname1, *fnames]:
                with open(directory / fname1) as f:
                    snap1 = ast.literal_eval(f.read())

                if fnames:
                    with open(directory / fnames[0]) as f:
                        snap2 = ast.literal_eval(f.read())
                else:
                    snap2 = cpu.snapshot()

                diffs = diff_snapshot(snap1, snap2)
                __import__('pprint').pprint(diffs)

            case ['giveall']:
                for addr in range(2670, 2734+1, 4):
                    cpu.memory[addr] = 0

            # write value to the STACK at address (0 = the bottom)
            case ['ws', addr, val]:
                cpu.stack[int(addr)] = int(val)

            # write value to MEMORY at address (0 = the bottom)
            case ['wm', addr, val]:
                cpu.memory[int(addr)] = int(val)

            # print memory
            case ['pm', addr, *nbytes]:
                addr = int(addr)
                nbytes = int(nbytes[0]) if nbytes else 1
                print(cpu.memory[addr:addr+nbytes])

            case ['reg']:
                print(cpu.registers)

            case ['ps', addr, *nbytes]:
                addr = int(addr)
                nbytes = int(nbytes[0]) if nbytes else 1
                print(cpu.stack[addr:addr+nbytes])

            case ['pinv']:
                for addr in range(2670, 2734+1, 4):
                    print(addr, cpu.memory[addr:addr+4])

            case ['dis', addr]:
                from disassembler import disassemble
                disassemble(cpu.memory, int(addr))

            case ['trace']:
                # TODO: Trace execution until next input/breakpoint
                pass

            case _:
                print('unknown debug command')

    except Exception as exc:
        print(exc)
