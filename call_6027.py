#!/usr/bin/env python3
import time
from multiprocessing import Pool, Event

# reference implementation of call 6027 which resembles the Ackermann function
def f(r0, r1, r7):
    if r0 == 0:
        return (r1 + 1) % 32768

    if r1 == 0:
        return f(r0 - 1, r7, r7)

    return f(r0 - 1, f(r0, r1 - 1, r7), r7)

# induction from simple cases:
#
#   f(0, B) = B + 1
#   f(1, B) = f(0, C) + B = B + C + 1
#   f(2, B) = f(1, f(2, B-1)) = B*(C+1) + 2*C + 1
#   f(3, B) = f(2, f(3, B-1)) cant be simplified, and the recursive branch goes from B to 0
#   f(3, B) depends on f(3, B-1) so we can apply DP. recursion is impractical (~32768 max call depth)

# working backwards from known inputs and the expected outcome:
#
#   f(4, 1) = 6
#   f(4, 1) = f(3, f(4, 0))
#           = f(3, f(3, C))
#
# thus we will be looking for f3[f3[C]] == 6

solution_found = Event()

def worker(start, end):
    for r7 in range(start, end):
        f3 = [0] * 32768
        f3[0] = (r7 * (r7 + 1) + 2 * r7 + 1) % 32768  # start with f(3, 0) = f(2, r7) from above eqs
        for i in range(1, 32768):
            f3[i] = (f3[i-1] * (r7 + 1) + 2 * r7 + 1) % 32768

        val = f3[f3[r7]]
        if val == 6:
            solution_found.set()
            return r7

        if solution_found.is_set():
            return

def worker_callback(result):
    if result is not None:
        print(f'Solution: r7 = {result}')

def main_multi():
    '''Multi-processing method which takes ~18s on my hardware'''

    processes = 8
    chunksize = 32768 // processes
    results = []

    print(f'Spawning {processes} processes...')

    with Pool(processes, initargs=(solution_found,)) as pool:
        for start in range(0, 32768, chunksize):
            args = (start, min(start + chunksize + 1, 32768))
            result = pool.apply_async(worker, args=args, callback=worker_callback)
            results.append(result)

        for result in results:
            result.get()

def main_single():
    '''Single-threaded method which takes ~3.5 min on my hardware'''

    last_val = 0
    last_time = time.time()

    for r7 in range(0, 32768):
        # print progress every second
        diff = time.time() - last_time
        if diff > 1:
            speed = (r7 - last_val) / diff
            eta = (32768 - r7) / speed / 60
            print('r7 = {}, {:.2f} it/sec, {:.2f} min left'.format(r7, speed, eta))
            last_val = r7
            last_time = time.time()

        f3 = [0] * 32768
        f3[0] = (r7 * (r7 + 1) + 2 * r7 + 1) % 32768  # f(3, 0) = f(2, r7)
        for i in range(1, 32768):
            f3[i] = (f3[i-1] * (r7 + 1) + 2 * r7 + 1) % 32768

        val = f3[f3[r7]]
        if val == 6:
            print(f'Solution: r7 = {r7}')
            break

if __name__ == '__main__':
    try:
        main_multi()
        # main_single()
    except KeyboardInterrupt:
        pass
