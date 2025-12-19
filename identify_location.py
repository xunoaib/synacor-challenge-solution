from itertools import pairwise

from helpers import diff_vms
from vm import VM

fname = 'challenge-aneurysm.bin'


def identify_location_addr(vm: VM):
    vm.run()
    vms = [vm]

    for cmd in ['doorway', 'north', 'north']:
        vms.append(vms[-1].sendcopy(cmd))

    loc_addr = None
    for a, b in pairwise(vms):
        mem = diff_vms(a, b)['memory']
        addrs = [d[0] for d in mem]
        loc_addr = addrs[0]  # assume lowest (may be incorrect)

    assert loc_addr
    return loc_addr


def main():

    vm = VM(fname)
    addr = identify_location_addr(vm)
    print(addr)

    # v2 = EnhancedCPU('challenge.bin')
    # v2.run()
    # addr = opcodes.find_teleporter_call(v2.memory)
    # print(addr)


if __name__ == '__main__':
    main()
