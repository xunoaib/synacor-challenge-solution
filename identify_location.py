from itertools import pairwise

import utils
from enhancedcpu import EnhancedCPU

fname = 'challenge-aneurysm.bin'


def identify_location_addr(vm: EnhancedCPU):
    vm.run()
    vms = [vm]

    for cmd in ['doorway', 'north', 'north']:
        vms.append(vms[-1].sendcopy(cmd))

    loc_addr = None
    for a, b in pairwise(vms):
        mem = utils.diff_vms(a, b)['memory']
        addrs = [d[0] for d in mem]
        loc_addr = addrs[0]  # assume lowest (may be incorrect)

    assert loc_addr
    return loc_addr


def main():

    vm = EnhancedCPU(fname)
    addr = identify_location_addr(vm)
    print(addr)

    # v2 = EnhancedCPU('challenge.bin')
    # v2.run()
    # addr = utils.find_teleporter_call(v2.memory)
    # print(addr)


if __name__ == '__main__':
    main()
