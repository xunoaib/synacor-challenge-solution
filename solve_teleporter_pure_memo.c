#include <stdio.h>
#include <string.h>

#define R0_MAX 10 // max is technically 4
#define R1_MAX 32768
#define UNSET -1

static int memo[R0_MAX][R1_MAX];

int f(int r0, int r1, int r7) {
    if (r0 == 0)
        return (r1 + 1) % 32768;

    if (memo[r0][r1] != UNSET)
        return memo[r0][r1];

    int result;
    if (r1 == 0) {
        result = f(r0 - 1, r7, r7);
    } else {
        result = f(r0 - 1, f(r0, r1 - 1, r7), r7);
    }

    memo[r0][r1] = result;
    return result;
}

int main() {
    int r0 = 4;
    int r1 = 1;

    for (int r7 = 0; r7 < 32768; r7++) {
        memset(memo, UNSET, sizeof(memo));
        int result = f(r0, r1, r7);
        printf("f(%d,%d,%d) = %d\n", r0, r1, r7, result);
        if (result == 6) {
            printf("Solution get!\n");
            break;
        }
    }

    return 0;
}
