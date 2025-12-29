from itertools import combinations, permutations

from z3 import Int, Or, Solver, sat

COIN_NAMES = {
    2: 'red coin',
    3: 'corroded coin',
    5: 'shiny coin',
    7: 'concave coin',
    9: 'blue coin',
}


def solve_coin_order():
    for a, b, c, d, e in permutations(COIN_NAMES):
        if a + b * c**2 + d**3 - e == 399:
            return [a, b, c, d, e]


def solve_coin_order_z3():
    a, b, c, d, e = vals = [Int(chr(ord('a') + i)) for i in range(5)]

    s = Solver()
    s.add(a + b * c**2 + d**3 - e == 399)
    s.add(x != y for x, y in combinations(vals, 2))
    s.add(Or([v == n for n in COIN_NAMES]) for v in vals)

    assert s.check() == sat
    m = s.model()
    return [m[v].as_long() for v in vals]


coins = solve_coin_order()
# coins = solve_coin_order_z3()

print('coin order:', coins, '\n')

for coin in coins:
    print('use', COIN_NAMES[coin])
