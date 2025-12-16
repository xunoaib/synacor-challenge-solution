from itertools import pairwise

import utils
from enhancedcpu import EnhancedCPU


def main():
    vm = EnhancedCPU('challenge-aneurysm.bin')
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


if __name__ == '__main__':
    main()
