from itertools import pairwise

import utils
from enhancedcpu import EnhancedCPU

fname = 'challenge-aneurysm.bin'


def identify_location_addr():
    vm = EnhancedCPU(fname)
    vm.run()
    vms = [vm]

    for cmd in ['doorway', 'north', 'north']:
        vms.append(vms[-1].sendcopy(cmd))

    for a, b in pairwise(vms):
        mem = utils.diff_vms(a, b)['memory']
        addrs = [d[0] for d in mem]
        # print(mem)
        print(addrs)

        loc_addr = addrs[0]  # assume lowest (may be incorrect)

    print(f'{loc_addr=}')
    # vm.interactive()


def identify_tele_call():

    # Code to search for (ignoring special memory addresses)
    code = [
        7, 32768, None, 9, 32768, 32769, 1, 18, 7, 32769, None, 9, 32768,
        32768, 32767, 1, 32769, 32775, 17, None, 18, 2, 32768, 9, 32769, 32769,
        32767, 17, None, 1, 32769, 32768, 3, 32768, 9, 32768, 32768, 32767, 17,
        None, 18
    ]

    v1 = EnhancedCPU(fname)
    v1.run()
    print(v1.memory[6049:6090])

    v2 = EnhancedCPU('challenge.bin')
    v2.run()
    print(v2.memory[6027:6027 + (6090 - 6049)])

    print(find_code(v1.memory, code))
    print(find_code(v2.memory, code))


def find_code(memory: list[int], code: list[int | None]):
    n = len(code)
    return [
        i for i in range(len(memory))
        if all(m == c for m, c in zip(memory[i:i + n], code) if c is not None)
    ]


def main():
    # identify_location_addr()
    identify_tele_call()


if __name__ == '__main__':
    main()
