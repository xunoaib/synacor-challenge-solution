import string

from vm import VM


def strings(memory: list[int]):
    addr_strs = {}
    laddr = 0

    for addr, v in enumerate(memory):
        if v < 256 and chr(v) in string.printable:
            addr_strs[laddr] = addr_strs.get(laddr, '') + chr(v)
        else:
            laddr = addr + 1

    return addr_strs


def main():
    vm = VM('challenge.bin')
    vm.run()

    addr_strs = strings(vm.memory)

    MIN_STR_LEN = 2

    for addr, s in addr_strs.items():
        if len(s) >= MIN_STR_LEN:
            print(addr, repr(s))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
