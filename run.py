import argparse

from vm import VM


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--commands')
    parser.add_argument('-f', '--file', default='challenge.bin')
    args = parser.parse_args()

    print('Loading binary:', args.file)

    vm = VM(args.file)
    print(vm.read())

    if args.commands:
        for cmd in args.commands.split(';'):
            vm.send(cmd.strip())
            print(vm.read())

    vm.interactive()


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError, BrokenPipeError):
        pass
