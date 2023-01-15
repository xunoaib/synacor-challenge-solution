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

COIN_VALS = [2, 3, 5, 7, 9]

def solve_coin_order():
    for a,b,c,d,e in permutations(COIN_VALS):
        if a + b * c**2 + d**3 - e == 399:
            return [a,b,c,d,e]

def solve_coin_order_z3():
    a,b,c,d,e = vals = [Int(chr(ord('a') + i)) for i in range(5)]

    s = Solver()
    s.add(a + b * c**2 + d**3 - e == 399)

    for x,y in combinations(vals, 2):
        s.add(x != y)

    for v in vals:
        s.add(Or([v == n for n in COIN_VALS]))

    m = s.model()
    return [m[v] for v in vals]


def main():
    coins = solve_coin_order()
    print('coin order:', coins, '\n')

    for coin in coins:
        print('use', COIN_NAMES[coin])

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
