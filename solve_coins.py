#!/usr/bin/env python3
from z3 import Solver, Int, Or
from itertools import combinations, permutations, pairwise

from enhancedcpu import EnhancedCPU
import utils

COIN_NAMES = {
    2: 'red coin',
    3: 'corroded coin',
    5: 'shiny coin',
    7: 'concave coin',
    9: 'blue coin',
}

def solve_coin_order():
    for a,b,c,d,e in permutations([2,3,5,7,9]):
        if a + b * c**2 + d**3 - e == 399:
            return [a,b,c,d,e]

def solve_coin_order_z3():
    a,b,c,d,e = vals = [Int(chr(ord('a') + i)) for i in range(5)]

    s = Solver()
    s.add(a + b * c**2 + d**3 - e == 399)

    for x,y in combinations(vals, 2):
        s.add(x != y)

    for v in vals:
        nums = [2, 3, 5, 7, 9]
        conds = [v == n for n in nums]
        s.add(Or(conds))

    m = s.model()
    return [m[v] for v in vals]


def main():
    coins = solve_coin_order()
    print('coin order:', coins)
    print()

    vm = EnhancedCPU.from_snapshot_file('snapshots/coins.blank')
    vm.debug_cmd('giveall')
    vms = [vm]

    for coin in coins:
        vms.append(vms[-1].sendcopy('use ' + COIN_NAMES[coin]))
        print(vms[-1].read().strip())
        diff = utils.diff_vms(*vms[-2:])
        __import__('pprint').pprint(diff)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
