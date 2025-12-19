import string

from vm import VM


def strings(memory: list[int], min_len: int):
    groups = {}
    laddr = 0

    for addr, v in enumerate(memory):
        if v < 256 and chr(v) in string.printable:
            groups[laddr] = groups.get(laddr, '') + chr(v)
        else:
            laddr = addr + 1

    for a, s in groups.items():
        if len(s) >= min_len:
            print(a, repr(s))


def main():
    vm = VM('challeng.bin')
    vm.run()
    strings(vm.memory, 2)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
