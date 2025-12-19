from itertools import batched

from opcodes import Opcode, is_reg, read_instruction, to_reg


def load_bytecode(binfile):
    with open(binfile, 'rb') as f:
        return [int.from_bytes(b, 'little') for b in batched(f.read(), 2)]


class Registers:

    def __init__(self):
        self._regs = [0] * 8

    def __getitem__(self, idx) -> int:
        return self._regs[idx]

    def __setitem__(self, idx, val):
        self._regs[idx] = val


class BaseVM:

    def __init__(self, binfile=None):
        self.memory = []
        self.registers = Registers()
        self.stack: list[int] = []
        self.pc: int = 0
        self.input_buffer: list[str] = []
        self.output_buffer: str = ''

        if binfile:
            self.memory = load_bytecode(binfile)

    def value(self, arg) -> int:
        return self.registers[arg - 32768] if is_reg(arg) else arg

    def set_reg(self, arg, value):
        self.registers[to_reg(arg)] = value

    def send(self, cmd) -> None:
        self.input_buffer = list(cmd + '\n')
        self.run()

    def read(self):
        result = self.output_buffer
        self.output_buffer = ''
        return result

    def run(self):
        while self.step():
            pass

    def step(self) -> bool:
        '''Returns False if halted or waiting for input'''
        return self.execute(*read_instruction(self.memory, self.pc))

    def execute(self, opcode: Opcode, args: tuple[int, ...]):
        '''Executes the given instruction and returns False if halted or
        waiting for input'''

        new_pc = self.pc + len(opcode)
        a, b, c = args + (0, ) * (3 - len(args))

        match opcode.name:
            case 'noop':
                pass

            case 'halt':
                return False

            case 'out':
                self.output_buffer += chr(self.value(a))

            case 'jmp':
                new_pc = a

            case 'jt':
                if self.value(a) != 0:
                    new_pc = b

            case 'jf':
                if self.value(a) == 0:
                    new_pc = b

            case 'set':
                self.set_reg(a, self.value(b))

            case 'add':
                self.set_reg(a, (self.value(b) + self.value(c)) % 32768)

            case 'eq':
                self.set_reg(a, int(self.value(b) == self.value(c)))

            case 'push':
                self.stack.append(self.value(a))

            case 'pop':
                self.set_reg(a, self.stack.pop())

            case 'gt':
                self.set_reg(a, int(self.value(b) > self.value(c)))

            case 'and':
                self.set_reg(a, int(self.value(b) & self.value(c)))

            case 'or':
                self.set_reg(a, int(self.value(b) | self.value(c)))

            case 'not':
                self.set_reg(a, ~self.value(b) & (2**15 - 1))

            case 'call':
                self.stack.append(new_pc)
                new_pc = self.value(a)

            case 'mult':
                self.set_reg(a, (self.value(b) * self.value(c)) % 32768)

            case 'mod':
                self.set_reg(a, self.value(b) % self.value(c))

            # read memory at address <b> and write it to <a>
            case 'rmem':
                self.set_reg(a, self.memory[self.value(b)])

            # write the value from <b> into memory at address <a>
            case 'wmem':
                self.memory[self.value(a)] = self.value(b)

            # remove the top element from the stack and jump to it; empty stack = halt
            case 'ret':
                if not self.stack:
                    return False
                new_pc = self.stack.pop()

            case 'in':
                # pause program when input buffer is empty
                if not self.input_buffer:
                    return False

                self.set_reg(a, ord(self.input_buffer.pop(0)))

            case _:
                raise NotImplementedError(
                    f'Not implemented: {opcode=} {args=}'
                )

        self.pc = new_pc
        return True
