# Synacor Challenge Solution

This repository contains my solution (and related files) for the [Synacor Challenge](https://github.com/xunoaib/synacor-challenge)

## ⚠️ Warning! Spoilers Ahead! ⚠️

Consider looking away if you have not already completed this challenge!

Synacor can only be completed once and is easily spoilable!

# Table of Contents

- [Source Files](#source-files)
- [Codes](#codes)
  - [Code 1: Architecture Spec](#code-1-architecture-spec)
  - [Code 2: Pre-Self-Test Code](#code-2-pre-self-test-code)
  - [Code 3: Post-Self-Test Code](#code-3-post-self-test-code)
  - [Code 4: Tablet](#code-4-tablet)
  - [Code 5: Twisty Maze](#code-5-twisty-maze)
  - [Code 6: Coins Puzzle](#code-6-coins-puzzle)
  - [Code 7: Teleporter](#code-7-teleporter)
    - [Live Instruction Trace](#live-instruction-trace)
    - [Disassembling the Call Site](#disassembling-the-call-site)
    - [Disassembling the Function @ 6027](#disassembling-the-function--6027)
    - [Analyzing the Teleporter Call](#analyzing-the-teleporter-call)
    - [Optimizing the Teleporter Call](#optimizing-the-teleporter-call)
      - [Memoization](#memoization)
      - [Further Analysis / Simplification](#further-analysis--simplification)
    - [Patching the Teleporter Call](#patching-the-teleporter-call)
  - [Code 8: Vault Puzzle](#code-8-vault-puzzle)
- [Extra Observations, Details, and Features](#extra-observations-details-and-features)
  - [Custom Commands](#custom-commands)
  - [Self-Test Decryption](#self-test-decryption)
  - [Memory Hacking](#memory-hacking)
  - [Map Visualizations](#map-visualizations)

# Source Files

Challenge Files:
- [arch-spec](arch-spec) -- Architecture specification
- [challenge.bin](challenge.bin) -- Challenge binary

VM Logic:
- [basevm.py](basevm.py) -- Base emulator implementing core VM functionality.
- [vm.py](vm.py) -- Enhanced emulator with extra features / debug commands.
- [run.py](run.py) -- Launches an interactive VM from a binary.
- [disassembler.py](disassembler.py) -- Disassembles a binary.

Solvers:
- [solve_all.py](solve_all.py) -- Executes an end-to-end solution for a given binary, printing all codes found.
- [solve_coins.py](solve_coins.py) -- Solves the ruins coin puzzle.
- [solve_teleporter_pure_memo.c](solve_teleporter_pure_memo.c) -- Solves the teleporter puzzle with pure memoization, no other optimizations (C).
- [solve_teleporter.py](solve_teleporter.py) -- Solves the teleporter puzzle after simplification (Python).
- [solve_teleporter.c](solve_teleporter.c) -- Solves the teleporter puzzlle after simplification (C).
- [solve_vault.py](solve_vault.py) -- Solves the vault puzzle.

# Codes

The challenge contains eight unique codes, each found by completing the following puzzles:

- **Code 1:** Found in `arch-spec`
- **Code 2:** VM pre-self-test
- **Code 3:** VM post-self-test
- **Code 4:** Tablet
- **Code 5:** Twisty Passages
- **Code 6:** Ruins Coin Puzzle
- **Code 7:** Teleporter
- **Code 8:** Vault

## Code 1: Architecture Spec

The first code appears in the hints section of the VM architecture spec
([`arch-spec`](arch-spec)). Amusingly, this was the last code I found.

## Code 2: Pre-Self-Test Code

Running the binary after implementing the `out` and `noop` instructions reveals
the pre-self-test code.

## Code 3: Post-Self-Test Code

Implementing the remaining VM instructions allows the self-test to complete,
revealing the next code.

Now that all instructions have been implemented, it seems we've been dropped
into a text-adventure game!

## Code 4: Tablet

Once the self-test completes, typing `take tablet` and `use tablet` reveals the
next code.

Note: For later puzzles, it's also important to collect the `empty lantern`
from the easternmost moss cavern.

## Code 5: Twisty Maze

Exploring the area reveals a ladder leading to twisty passages. At first, the
maze seems unpredictable, with different exits leading to unexpected locations.
In reality, however, the maze is fully deterministic and can be systematically
mapped by recording our current location, moving in a new direction, and noting
the resulting location -- repeating this process until every area has been
discovered. Fortunately, each location has a description that is very similar
to the others but contains subtle differences, allowing each spot to be
uniquely identified.

Eventually, we will find a passage with a code chiseled into the wall, along
with a can of oil, which should be taken. Notably, the code is only valid if we
reach this location through legitimate in-game commands; using cheats or
location hacks (such as modifying memory) will cause an incorrect code to
appear.

Below is a visualization of the maze, with the rightmost red node indicating
the location of the code and the can of oil. For a complete map of all
accessible locations at each stage of the game, see the [Map
Visualizations](#map-visualizations) section.

![](maps/twisty_maze_crop.png)


We can now refuel and light the lantern (`use can`, then `use lantern`), and
safely navigate the dark passage into the ruins.

## Code 6: Coins Puzzle

In the central hall, we encounter a cryptic equation featuring symbols and
circular slots:

    _ + _ * _^2 + _^3 - _ = 399

To solve it, we must place five coins into the slots in the correct order. Each
coin can be collected from other rooms in the ruins, and examining a coin
(`look <coin>`) reveals its numerical value:

- red coin: 2 dots
- corroded coin: triangle (3 dots)
- shiny coin: pentagon (5 dots)
- concave coin: 7 dots
- blue coin: 9 dots

The correct sequence can be found using [brute-force (even z3)](solve_coins.py)
or sheer mental reasoning:

    9 + 2 * 5^2 + 7^3 - 3 = 399

Place the coins in the following order to unlock the north door:

```
use blue coin
use red coin
use shiny coin
use concave coin
use corroded coin
```

A click echoes as the north door unlocks. We go north, take the teleporter,
then use it. As we spiral through time and space, the next code appears in the
stars!

## Code 7: Teleporter

The teleporter brings us to Synacor Headquarters, which appears to be a really
fun place to work. The strange book here also reveals some hidden behavior of
the teleporter:

<details>
    <summary>🔽 look strange book</summary>

```
The cover of this book subtly swirls with colors.  It is titled "A Brief
Introduction to Interdimensional Physics".  It reads:

Recent advances in interdimensional physics have produced fascinating
predictions about the fundamentals of our universe!  For example,
interdimensional physics seems to predict that the universe is, at its root, a
purely mathematical construct, and that all events are caused by the
interactions between eight pockets of energy called "registers".
Furthermore, it seems that while the lower registers primarily control mundane
things like sound and light, the highest register (the so-called "eighth
register") is used to control interdimensional events such as teleportation.

A hypothetical such teleportation device would need to have have exactly two
destinations.  One destination would be used when the eighth register is at its
minimum energy level - this would be the default operation assuming the user
has no way to control the eighth register.  In this situation, the teleporter
should send the user to a preconfigured safe location as a default.

The second destination, however, is predicted to require a very specific
energy level in the eighth register.  The teleporter must take great care to
confirm that this energy level is exactly correct before teleporting its user!
If it is even slightly off, the user would (probably) arrive at the correct
location, but would briefly experience anomalies in the fabric of reality
itself - this is, of course, not recommended.  Any teleporter would need to test
the energy level in the eighth register and abort teleportation if it is not
exactly correct.

This required precision implies that the confirmation mechanism would be very
computationally expensive.  While this would likely not be an issue for large-
scale teleporters, a hypothetical hand-held teleporter would take billions of
years to compute the result and confirm that the eighth register is correct.

If you find yourself trapped in an alternate dimension with nothing but a
hand-held teleporter, you will need to extract the confirmation algorithm,
reimplement it on more powerful hardware, and optimize it.  This should, at the
very least, allow you to determine the value of the eighth register which would
have been accepted by the teleporter's confirmation mechanism.

Then, set the eighth register to this value, activate the teleporter, and
bypass the confirmation mechanism.  If the eighth register is set correctly, no
anomalies should be experienced, but beware - if it is set incorrectly, the
now-bypassed confirmation mechanism will not protect you!

Of course, since teleportation is impossible, this is all totally ridiculous.

```
</details>

This tells us that we must write a specific value to the eighth register before
using the teleporter again, and that we may also need to optimize the
underlying code somehow.

For now, we can assign an arbitrary value to the eighth register and use the
teleporter to see what happens. For this purpose, I created a custom `.wr <reg>
<value>` command in my VM:

```
> .wr 7 1234
> use teleporter

A strange, electronic voice is projected into your mind:

  "Unusual setting detected!  Starting confirmation process!  Estimated time to completion: 1 billion years."
```

This causes the VM to hang indefinitely, and my CPU fan indicates that it's
doing some heavy work.

### Live Instruction Trace

To see what our VM is doing, we can print the address and disassembly of each
instruction as it's being executed. Inspecting the output, we notice an
excessive number of repeating calls to a function at address 6027 (the `call
6027` instruction). Here's a live log of the instructions being executed,
starting right before the first call to this function. For clarity, each call
to 6027 is marked with a 👈.

<details>
    <summary><strong>🔽 Live Instruction Trace:</strong></summary>

```
address | instruction
...
5478 noop 
5479 noop 
5480 noop 
5481 noop 
5482 noop 
5483 set r0 4
5486 set r1 1
5489 call 6027 👈 (first call)
6027 jt r0 6035
6035 jt r1 6048
6048 push r0
6050 add r1 r1 32767
6054 call 6027 👈
6027 jt r0 6035
6035 jt r1 6048
6038 add r0 r0 32767
6042 set r1 r7
6045 call 6027 👈
6027 jt r0 6035
6035 jt r1 6048
6048 push r0
6050 add r1 r1 32767
6054 call 6027 👈
6027 jt r0 6035
6035 jt r1 6048
6048 push r0
6050 add r1 r1 32767
6054 call 6027 👈
6027 jt r0 6035
6035 jt r1 6048
6048 push r0
6050 add r1 r1 32767
6054 call 6027 👈
... (continues)
```
</details>

### Disassembling the Call Site

Given the lack of `ret` instructions after each `call 6027` in the above trace,
we may deduce that this function is recursive. In this case, instead of a live
disassembly, it may be more helpful to analyze a static disassembly of this
function (at address 6027) and the region where it is first called (address
5489):

Analyzing the initial call site, we have:

```
5483  set r0 4
5486  set r1 1
5489  call 6027  👈 <- calls function @ 6027
5491  eq r1 r0 6 ⭐ <- checks if r0 == 6
5495  jf r1 5579    <- if above check failed (r0 != 6), jumps to 5579
5498  push r0       <- otherwise, continues here (presumably, the "good" path)
5500  push r1
5502  push r2
5504  set r0 29014
5507  set r1 1531
5510  add r2 1816 12241
5514  call 1458
```

Before the first call to this function, we see that the value 4 is written to
register 0, and 1 is written to register 1. The function at 6027 is then
called, and once it returns, the VM checks if register 0 now contains a value
of 6, jumping to address 5579 if false (`r0 != 6`), or continuing to address
5498 if true (`r0 == 6`). We can infer that the truthy path is the desired path
(where `r0 == 6`). We can confirm this by independently tracing each branch to
completion, though these steps have been omitted for brevity.

Judging from this code, the output of the function is likely stored in `r0`, and
its value is likely expected to be 6 given the observed inputs (`r0 = 4`, `r1 = 1`,
and `r7 = ?`). However, the correct input value for the eighth register (`r7`) is
still unknown.

Our goal appears to be twofold:
1. Find the correct value of `r7` which causes the initial function call to
   return 6 (stored in `r0`).
2. Ensure this function call completes in a reasonable time (before the heat
   death of the universe).

### Disassembling the Function @ 6027

Here's a complete disassembly of the function at address 6027:

```
6027  jt r0 6035
6030  add r0 r1 1
6034  ret
6035  jt r1 6048
6038  add r0 r0 32767
6042  set r1 r7
6045  call 6027
6047  ret
6048  push r0
6050  add r1 r1 32767
6054  call 6027
6056  set r1 r0
6059  pop r0
6061  add r0 r0 32767
6065  call 6027
6067  ret
```

### Analyzing the Teleporter Call

To simplify our analysis, we can rewrite the recursive 6027 function in Python:

```python
# We can treat R7 (the eighth register) as a global constant,
# since the function never modifies it.

def f(r0, r1):
    if r0 == 0: return (r1 + 1) % 32768
    if r1 == 0: return f(r0 - 1, R7)
    return f(r0 - 1, f(r0, r1 - 1))
```

Educated readers may recognize this as a slight variation of the [Ackermann
Function](https://en.wikipedia.org/wiki/Ackermann_function), though I did not!

This function is extremely recursive and has a very high time complexity.

### Optimizing the Teleporter Call

To restate our objective, based on our prior observations (the initial inputs
of the function known to be `r0 = 4`, `r1 = 1`, and its expectation to return
`6`), we will be looking for a value of `r7` which produces `f(4, 1) == 6`

#### Memoization

To speed up execution of highly recursive functions like this (having many
redudant subtrees), we can use
[memoization](https://en.wikipedia.org/wiki/Memoization) to cache the result
of each function call and avoid doing redundant work. With memoization, we can
more easily brute-force input values of `r7` for this function (between 0 and
32768), searching for one which returns the expected output: 6.

This can be easily implemented in C or Java with a sufficiently large stack:
[solve_teleporter_pure_memo.c](solve_teleporter_pure_memo.c), where the
solution can be found in roughly 10 seconds on my hardware.

#### Further Analysis / Simplification

However, I'm a man of Python, and in Python, naively caching recursive calls
turns out not to be ideal here. Even with `functools.cache` and an increased
recursion limit, Python still hits a `RecursionError` for deeper invocations of
the function. Manual memoization avoids this issue, but the resulting
performance is **extremely** slow (~75 function calls per second). At that
rate, brute-forcing all 32,768 possible values of `r7` would take about 7
minutes -- doable, but unpleasant.

Rather than waiting, this gives us an opportunity to look inside the recurrence
and simplify its structure.

By progressively substituting simpler forms into more complex calls, we can
identify patterns that let us rewrite and compress the computation. The
following identities summarize the recurrence at its most fundamental level:

**Base and general recurrence:**

    f(0, B) = B + 1
    f(A, 0) = f(A-1, R7)
    f(A, B) = f(A-1, f(A, B-1))

**Simplifying `f(1, B)`**

Repeatedly applying the base case `f(0, B) = B + 1` allows us to unroll the recursion:

    f(1, B) = f(0, f(1,B-1))
            = f(1, B-1) + 1
            = f(0, f(1,B-2)) + 1
            = f(1, b-2) + 2
            = f(0, f(1,B-3)) + 2
            = f(1, B-3) + 3
            = ...
            = f(1, B-n) + n
            = ...
            = f(1, B-B) + B
            = f(1, 0) + B  <- matches f(A, 0) case
            = f(0, R7) + B
            = R7 + 1 + B

So:

    f(1, B) = R7 + 1 + B

This confirms that the first level of recursion behaves like a simple linear
function of `B`, offset by `R7 + 1`.

**Simplifying `f(2, B)`**

Substituting the `f(1, X)` rule back into the recurrence:

    f(2, B) = f(1, f(2, B-1))
            = R7 + 1 + f(2, B-1)
            = R7 + 1 + f(1, f(2, B-2))
            = 2*(R7 + 1) + f(2, B-2)
            = 2*(R7 + 1) + f(1, f(2, B-3))
            = 3*(R7 + 1) + f(2, B-3)
            = ...
            = n*(R7 + 1) + f(2, B-n)
            = ...
            = B*(R7 + 1) + f(2, B-B)
            = B*(R7 + 1) + f(2, 0)   matches f(A, 0) case
            = B*(R7 + 1) + f(1, R7)
            = B*(R7 + 1) + R7 + 1 + R7
            = B*(R7 + 1) + 2*R7 + 1

So:

    f(2, B) = B*(R7 + 1) + 2*R7 + 1

**Attempting to simplify `f(3, B)`**

Applying the same approach to `f(3, B)` quickly becomes cumbersome:

    f(3, B) = f(2, f(3, B-1))  <- matches f(2, B) case
            = f(3, B-1) + 2*R7 + 1
            = f(2, f(3, B-2)) + 2*R7 + 1  <- matches f(2, B) case
            = [f(3,B-2) * (R7+1)+1] + 2*R7 + 1
            = f(3,B-2) * (R7+1) + 2*R7 + 2
            = f(2, f(3,B-3)) * (R7+1) + 2*R7 + 2
            = [f(3,B-3) * (R7+1) + 2*R7 + 1] * (R7+1) + 2*R7 + 2
            = f(3,B-3) * (R7+1)^2 + 2*R7*(R7+1) + R7+1 + 2*R7 + 2
            = f(3,B-3) * (R7+1)^2 + 2*R7*(R7+1) + 3*R7 + 3
            = ... (increasingly nested terms)

While a closed form is possible, the expression grows rapidly and loses
clarity. More importantly, we can observe a key structural property without
finishing the algebra:

`f(3, B)` depends only on `f(3, B-1)`, rather than branching recursively. The
depth of substitution is therefore at most `B` (<=32,768), with no exponential
blow-up. In other words, `f(3, B)` is **computationally cheap to evaluate**, even
across all possible values of `R7`.

**Using the recurrence to solve the teleporter**

With that insight, we can work backwards from the target expression:

    f(4, 1) = 6
    f(4, 1) = f(3, f(4, 0))
            = f(3, f(3, R7))

So we're looking for an `R7` such that:

    f(3, f(3, R7)) == 6

Since evaluating `f(3, X)` is manageable for all `X`, we can brute-force `R7`.

See [solve_teleporter.py](solve_teleporter.py) and
[solve_teleporter.c](solve_teleporter.c) for the simplified solver, and
[solve_teleporter_pure_memo.c](solve_teleporter_pure_memo.c) for the original
naive-memoization approach.

After all this work, the secret value of `r7` is revealed to be **25734**! ⭐

### Patching the Teleporter Call

We now know the correct input value for `r7`, but simply writing this value to
`r7` is not enough. The function is still extremely slow; We need to skip the
expensive call. Fortunately, now that we know the expected inputs and outputs
of this function, there is no need to actually execute it. Instead, we can add
VM logic to skip the `call 6027` instruction when it is encountered, and write
the expected post-call values into the appropriate registers (`r0`, `r1` and
`r7`). This allows us to replicate the behavior of the function without
actually executing it.

After patching the call, we can set `r7` to the secret value 25734, then use
the teleporter again, which brings us to a new location: the beach!

```
> .wr 7 25734
> use teleporter
```

## Code 8: Vault Puzzle

A path leads from the beach into the tropical island, a tropical cave, and then
finally the vault. A journal can also be found in a tropical cave alcove along
the way, containing hints for the vault puzzle:

<details>
    <summary>🔽 look journal</summary>

```
Fireflies were using this dusty old journal as a resting spot until you scared
them off.  It reads:

Day 1: We have reached what seems to be the final in a series of puzzles
guarding an ancient treasure.  I suspect most adventurers give up long before
this point, but we're so close!  We must press on!

Day 1: P.S.: It's a good thing the island is tropical.  We should have food for
weeks!

Day 2: The vault appears to be sealed by a mysterious force - the door won't
budge an inch.  We don't have the resources to blow it open, and I wouldn't
risk damaging the contents even if we did.  We'll have to figure out the lock
mechanism.

Day 3: The door to the vault has a number carved into it.  Each room leading up
to the vault has more numbers or symbols embedded in mosaics in the floors.  We
even found a strange glass orb in the antechamber on a pedestal itself labeled
with a number.  What could they mean?

Day 5: We finally built up the courage to touch the strange orb in the
antechamber.  It flashes colors as we carry it from room to room, and sometimes
the symbols in the rooms flash colors as well.  It simply evaporates if we try
to leave with it, but another appears on the pedestal in the antechamber
shortly thereafter.  It also seems to do this even when we return with it to
the antechamber from the other rooms.

Day 8: When the orb is carried to the vault door, the numbers on the door flash
black, and then the orb evaporates.  Did we do something wrong?  Doesn't the
door like us?  We also found a small hourglass near the door, endlessly
running.  Is it waiting for something?

Day 13: Some of my crew swear the orb actually gets heaver or lighter as they
walk around with it.  Is that even possible?  They say that if they walk
through certain rooms repeatedly, they feel it getting lighter and lighter, but
it eventually just evaporates and a new one appears as usual.

Day 21: Now I can feel the orb changing weight as I walk around.  It depends on
the area - the change is very subtle in some places, but certainly more
noticeable in others, especially when I walk into a room with a larger number
or out of a room marked '*'.  Perhaps we can actually control the weight of
this mysterious orb?

Day 34: One of the crewmembers was wandering the rooms today and claimed that
the numbers on the door flashed white as he approached!  He said the door still
didn't open, but he noticed that the hourglass had run out and flashed black.
When we went to check on it, it was still running like it always does.  Perhaps
he is going mad?  If not, which do we need to appease: the door or the
hourglass?  Both?

Day 55: The fireflies are getting suspicious.  One of them looked at me funny
today and then flew off.  I think I saw another one blinking a little faster
than usual.  Or was it a little slower?  We are getting better at controlling
the weight of the orb, and we think that's what the numbers are all about.  The
orb starts at the weight labeled on the pedestal, and goes down as we leave a
room marked '-', up as we leave a room marked '+', and up even more as we leave
a room marked '*'.  Entering rooms with larger numbers has a greater effect.

Day 89: Every once in a great while, one of the crewmembers has the same story:
that the door flashes white, the hourglass had already run out, it flashes
black, and the orb evaporates.  Are we too slow?  We can't seem to find a way
to make the orb's weight match what the door wants before the hourglass runs
out.  If only we could find a shorter route through the rooms...

Day 144: We are abandoning the mission.  None of us can work out the solution
to the puzzle.  I will leave this journal here to help future adventurers,
though I am not sure what help it will give.  Good luck!

What do you do?

```
</details>

We enter the vault antechamber through a southwest corner (lower left), which
contains a pedestal on which '22' is carved and on which rests a mysterious orb
(which can be taken). Exploring the vault also reveals a 4x4 grid of rooms
containing numbers/symbols in the following configuration:


| **\***  | **8** | **-**  | **1**  |
|:------:|:-----:|:-----:|:-----:|
| **4**  | **\*** | **11** | **\***  |
| **+**  | **4** | **\-**  | **18** |
| **22** | **\-** | **9**  | **\***  |


The vault door is located at the northeast corner (upper right) and has a large
'30' carved into it. This hints that the goal may be to arrive at the vault
door with a value of 30. Based on the journal entries, we also understand that
we can pick up the orb (whose value starts at 22), and travel between different
rooms to modify its value. For example, we can pick up the orb (starting with a
value of 22), then travel north (to '+'), then east (to '4'), to perform the
operation: 22 + 4, which produces a new value of 26. This pattern can be
repeated to modify the value of the orb, with the goal of arriving at the upper
right corner with a value of 30.

We can observe some rules:
- The orb disappears if its value would become negative.
- The starting room (vault antechamber) can't be visited twice (the orb
resets).
- The ending room (vault door) can't be visited before the puzzle is solved.
- After a certain number of steps, the orb evaporates. This forces us to find a
solution which uses a **minimal number of steps**. What fun!

**Optional:** By inspecting memory, we can also find that the orb's value is
stored at memory address `3952` (which differs across binaries).

To identify the shortest path from the antechamber to the goal, we can apply
[BFS](https://en.wikipedia.org/wiki/Breadth-first_search) (see
[solve_vault.py](solve_vault.py)):

```
take orb
north
east
east
north
west
south
east
east
west
north
north
east
vault
```

As we approach the vault door, the number on the vault door flashes white! The
hourglass is still running! It flashes white! We hear a click from the vault
door. The orb evaporates out of our hands.

We enter the vault, take the mirror, then use the mirror:

```
You gaze into the mirror, and you see yourself gazing back.  But wait!  It looks like someone wrote on your face while you were unconscious on the beach!  Through the mirror, you see "xxxxxxxxxxxx" scrawled in charcoal on your forehead.
```
 
Hooray! However, submitting this code reveals that it is not correct 🤔. Upon
reflection, we realize that because we are observing it through a mirror, the
message is likely mirrored. Most of the letters are symmetrical, except for a
few which must be flipped (`p`/`q`, `b`/`d`, etc). After making these
adjustments, we submit the correct and final code!

# Extra Observations, Details, and Features

## Custom Commands

The [vm.py](vm.py) and [basevm.py](basevm.py) files provide the primary APIs through which a VM can be created and manipulated.

Calling `vm.interactive()` drops the user into an interactive environment where
all input is passed to the VM via `vm.send(...)`, and all output is displayed
immediately.

Additional interactive commands are implemented to assist with debugging:

- `.save <fname>` -- Saves a complete snapshot of the VM state to `snapshots/<fname>` (including memory, stack, registers, pc, etc).
- `.load <fname>` -- Loads a VM snapshot from `snapshots/<fname>`.
- `.bp` or `.breakpoint` -- Executes `breakpoint()` for direct Python debugging.
- `.ws <addr> <val>` -- Write a value to the stack at the given address.
- `.wr <regid> <val>` -- Write a value to the register with the given zero-based index.
- `.wm <addr> <val>` -- Write a value to memory at the given address.
- `.pm <addr> [nbytes or 1]` -- Print nbytes of memory from the given address.
- `.reg` -- Print all registers.
- `.loc` -- Print the value of the current map location.
- `.loc <newloc>` -- Change the current map location to a new value.
- `.dis <lines> <addr>` -- Disassemble a number of instructions starting from the given address.
- `.macro <fname>` -- Execute the macro stored in `macros/<fname>`.
- Command aliases (`n`/`s`/`e`/`w` => `north`/`south`/`east`/`west`) to reduce typing.
- Chaining of multiple commands in a single line with `;`

## Self-Test Decryption

Very little information can be gleaned from `challenge.bin` in its initial
state. However, after running the self-test, the VM memory appears to be
completely transformed into a more interpretable format. This reveals that the
self-test performs some kind of self-decoding/self-decryption algorithm on both
code and memory.

## Memory Hacking

While mostly unnecessary, it's possible to inspect and manipulate some data in
memory, for example, to change the current player's location, modify inventory,
and retrieve plaintext strings from memory. However, be warned: the VM protects
against some memory hacks by corrupting codes which are not obtained "legally".

The current location, and whether each item is present in the player's
inventory, are stored in specific memory addresses which vary across binaries.

The memory address corresponding to a given item or location can be identified
by taking a snapshot of the current VM's state (i.e. with `.save state1`),
performing an action (i.e. `take tablet` or `go north`), then taking another
snapshot (`.save state2`), and performing a diff between them (with `.diff
state1 state2`).

If an item is present in the user's inventory, its value in memory will be 0.
For example, after running the self test, typing `.wm 2670 0` will give the
player a tablet. As an aside, item addresses also appear to be stored at 4-byte
intervals.

Notable memory addresses:

| Address | Description |
| --- | --- |
| 2732 | Map Location |
| 3952 | Orb value |

Item addresses (set their value to 0 to acquire the item):

| Address | Description |
| --- | --- |
|2670 | tablet|
|2674 | empty lantern|
|2678 | lantern|
|2682 | lit lantern|
|2686 | can|
|2690 | red coin|
|2694 | corroded coin|
|2698 | shiny coin|
|2702 | concave coin|
|2706 | blue coin|
|2710 | teleporter|
|2714 | business card|
|2718 | orb|
|2726 | strange book|
|2730 | journal|

## Map Visualizations

The [maps](maps/) directory contains visualizations of accessible locations
at each stage of the challenge, as new areas are unlocked.

**1. Initial Exploration (no items)**

![](maps/images/map0.html.png)

**2. After Lighting Lantern**

![](maps/images/map1.html.png)

**3. After Solving Coins Puzzle**

![](maps/images/map2.html.png)

**4. After First Teleportation**

![](maps/images/map3.html.png)

**5. After Second Teleportation**

![](maps/images/map4.html.png)

**6. After Unlocking Vault**

![](maps/images/map5.html.png)