import ast
import copy

from utils import to_register, isreg, read_instruction, load_bytecode


class CPU:
    def __init__(self, fname=None):
        self.memory = []
        self.registers = [0] * 8
        self.stack = []
        self.pc = 0  # program counter
        self.output_buffer = ''
        self.input_buffer = []  # keyboard input buffer

        if fname:
            self.load_program(fname)

    def load_program(self, fname):
        self.memory = load_bytecode(fname)
        self.pc = 0

    def readvalue(self, arg):
        if isreg(arg):
            return self.registers[arg - 32768]
        return arg

    @property
    def location(self):
        return self.memory[2732]

    @location.setter
    def location(self, value: int):
        self.memory[2732] = value

    def input(self):
        self.send(input('cpu> '))

    def send(self, data):
        self.input_buffer = list(data + '\n')
        self.run()

    def read(self):
        result = self.output_buffer
        self.output_buffer = ''
        return result

    def run(self):
        while self.step():
            pass

    def get_next_instruction(self):
        return read_instruction(self.memory, self.pc)

    def step(self):
        opcode, args = self.get_next_instruction()
        return self.execute(opcode, args)

    def execute(self, opcode, args):
        '''
        Executes the given instruction, updates the program counter, and
        returns true if the program has not halted.
        '''
        nextpc = self.pc + len(opcode)
        a, b, c = args + (None,) * (3 - len(args))

        match opcode.name:
            case 'noop':
                pass

            case 'halt':
                return False

            case 'out':
                a = self.readvalue(a)
                # print(chr(a), end='', flush=True)
                self.output_buffer += chr(a)

            case 'jmp':
                nextpc = a

            case 'jt':
                a = self.readvalue(a)
                if a != 0:
                    nextpc = b

            case 'jf':
                a = self.readvalue(a)
                if a == 0:
                    nextpc = b

            case 'set':
                a = to_register(a)
                b = self.readvalue(b)
                self.registers[a] = b

            case 'add':
                a = to_register(a)
                b = self.readvalue(b)
                c = self.readvalue(c)
                self.registers[a] = (b + c) % 32768

            case 'eq':
                a = to_register(a)
                b = self.readvalue(b)
                c = self.readvalue(c)
                self.registers[a] = int(b == c)

            case 'push':
                a = self.readvalue(a)
                self.stack.append(a)

            case 'pop':
                a = to_register(a)
                self.registers[a] = self.stack.pop()

            case 'gt':
                a = to_register(a)
                b = self.readvalue(b)
                c = self.readvalue(c)
                self.registers[a] = int(b > c)

            case 'and':
                a = to_register(a)
                b = self.readvalue(b)
                c = self.readvalue(c)
                self.registers[a] = int(b & c)

            case 'or':
                a = to_register(a)
                b = self.readvalue(b)
                c = self.readvalue(c)
                self.registers[a] = int(b | c)

            case 'not':
                a = to_register(a)
                b = self.readvalue(b)
                self.registers[a] = ~b & (2**15-1)

            case 'call':
                self.stack.append(nextpc)
                nextpc = self.readvalue(a)

            case 'mult':
                a = to_register(a)
                b = self.readvalue(b)
                c = self.readvalue(c)
                self.registers[a] = (b * c) % 32768

            case 'mod':
                a = to_register(a)
                b = self.readvalue(b)
                c = self.readvalue(c)
                self.registers[a] = (b % c)

            # read memory at address <b> and write it to <a>
            case 'rmem':
                a = to_register(a)
                b = self.readvalue(b)
                self.registers[a] = self.memory[b]

            # write the value from <b> into memory at address <a>
            case 'wmem':
                a = self.readvalue(a)
                b = self.readvalue(b)
                self.memory[a] = b

            # remove the top element from the stack and jump to it; empty stack = halt
            case 'ret':
                if not self.stack:
                    return False
                nextpc = self.stack.pop()

            # read a character from the terminal and write its ascii code to <a>; it can
            # be assumed that once input starts, it will continue until a newline is
            # encountered; this means that you can safely read whole lines from the
            # keyboard and trust that they will be fully read
            case 'in':
                # pause program when input buffer is empty
                if not self.input_buffer:
                    return False

                a = to_register(a)
                self.registers[a] = ord(self.input_buffer.pop(0))

            case _:
                print('unimplemented:', opcode, args)
                return False

        self.pc = nextpc
        return True

    def snapshot(self):
        return {
            'memory': self.memory,
            'stack': self.stack,
            'registers': self.registers,
            'pc': self.pc,
            'input_buffer': self.input_buffer,
            'output_buffer': self.input_buffer,
        }

    def clone(self):
        snapshot = self.snapshot()
        return self.__class__.from_snapshot(snapshot)

    def load_snapshot(self, snapshot: dict):
        for attrib in ['memory', 'stack', 'registers', 'pc', 'input_buffer']:
            setattr(self, attrib, copy.deepcopy(snapshot[attrib]))

    def __repr__(self):
        return f'<{self.__class__.__name__}(pc={self.pc}, loc={self.location})>'

    @staticmethod
    def read_snapshot(fname):
        with open(fname) as f:
            return ast.literal_eval(f.read())

    @classmethod
    def from_snapshot_file(cls, fname):
        snapshot = cls.read_snapshot(fname)
        return cls.from_snapshot(snapshot)

    @classmethod
    def from_snapshot(cls, snapshot):
        vm = cls()
        vm.load_snapshot(snapshot)
        return vm
