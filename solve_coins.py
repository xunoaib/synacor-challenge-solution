#!/usr/bin/env python3
from z3 import Solver, Int, sat, Or
from itertools import combinations, permutations

def solve_perm():
    for a,b,c,d,e in permutations([2,3,5,7,9]):
        if a + b * c**2 + d**3 - e == 399:
            print([a,b,c,d,e])
            return

def solve_z3():
    a,b,c,d,e = vals = [Int(chr(ord('a') + i)) for i in range(5)]

    s = Solver()
    s.add(a + b * c**2 + d**3 - e == 399)

    for x,y in combinations(vals, 2):
        s.add(x != y)

    for v in vals:
        nums = [2, 3, 5, 7, 9]
        conds = [v == n for n in nums]
        s.add(Or(conds))

    while s.check() == sat:
        m = s.model()
        ans = [m[v] for v in vals]
        print(ans)

        block = []
        for var in m:
            block.append(var() != m[var])
        s.add(Or(block))

def main():
    solve_perm()
    # solve_z3()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
