#!/usr/bin/env python3
import re
import pickle
from heapq import heappush, heappop

from enhancedcpu import EnhancedCPU

def next_states(vm: EnhancedCPU):
    exits = get_exits(vm)
    vms = []
    for direction in exits:
        n = vm.sendcopy(direction)
        vms.append((direction, n))
    return vms

def get_exits(vm: EnhancedCPU):
    vm.read()
    vm = vm.sendcopy('look')
    data = vm.read()
    if exitsstr := re.search(r'\nThere (is|are) (\d+) exits?:\n(.*)\nWhat do you do?', data, re.DOTALL):
        return re.findall(r'- (.*?)\n', exitsstr.group(3))
    return []

def explore(current: EnhancedCPU):
    '''Explore all possible paths from the given CPU state. Cycles are skipped'''

    current.read()
    current.send('look')

    vms = {}
    edges = {}  # maps current vm location => [(north_room_id, 'north'), ...]
    descriptions = {current.location: current.read().strip()}

    q = [current]

    while q:
        current = q.pop(0)
        print(current.location, descriptions[current.location].split('\n')[0])
        print(descriptions[current.location])

        states = list(next_states(current))
        edges[current.location] = [(neighbor.location, next_move) for next_move, neighbor in states]
        for _, neighbor in states:
            if neighbor.location not in vms:
                neighbor.read()
                neighbor.send('look')
                descriptions[neighbor.location] = neighbor.read().strip()
                vms[neighbor.location] = neighbor
                q.append(neighbor)

    return edges, descriptions, vms

# def find_path(edges: dict, src_vm: EnhancedCPU, tar_loc):
#     q = [(0, src_vm.location)]
#
#     while q:
#         cost, loc = heappop(q)

def main():
    # vm = EnhancedCPU('challenge.bin')
    # vm = EnhancedCPU.from_snapshot_file('snapshots/start')
    # vm.send('.giveall')
    # vm = EnhancedCPU.from_snapshot_file('snapshots/ladder')
    vm = EnhancedCPU.from_snapshot_file('snapshots/beach')
    edges, descs, vms = explore(vm)
    return

    # # discover all rooms (and cache to file)
    # vm = EnhancedCPU.from_snapshot_file('snapshots/beach')
    # vm.run()
    # edges, descs, vms = explore(vm)

    # with open('graph.pickle', 'wb') as f:
    #     f.write(pickle.dumps(ret))

    # # # load cached results generated above
    # with open('graph.pickle','rb') as f:
    #     ret = edges, descs, vms = pickle.loads(f.read())

    # print()
    # __import__('pprint').pprint(edges)

    for loc, desc in descs.items():
        # if 'Vault Door' in desc:
        #     print(loc)
        #     vms[loc].send('.save vault')

        # if 'journal' in desc:
        #     print(desc)
        #     vms[loc].interactive()
        print()
        print(desc)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
