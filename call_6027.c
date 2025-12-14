#include <math.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>

int done = 0;
int thread_count = 0;

void *compute_f3(void *arg) {
    long thread_id = (long)arg;
    long f3[32768];
    for (int i = 0; i < 32768; f3[i++]=0);

    long start = thread_id * 32768 / thread_count;
    long end = start + 32768 / thread_count;

    if (thread_id + 1 == thread_count)
        end = 32768;

    for (int r7 = start; r7 < end && !done; r7++) {
        f3[0] = (r7 * (r7 + 1) + 2 * r7 + 1) % 32768;
        for (int i = 1; i < 32768; i++)
            f3[i] = (f3[i-1] * (r7 + 1) + 2 * r7 + 1) % 32768;

        if (f3[f3[r7]] == 6) {
            printf("Solution found: %d\n", r7);
            done = 1;
            break;
        }
    }
    pthread_exit(0);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) {
        printf("Please specify one argument (number of threads).\n");
        return 1;
    }

    thread_count = atoi(argv[1]);
    pthread_t threads[thread_count];

    for (long i = 0; i < thread_count; i++)
        pthread_create(&threads[i], NULL, &compute_f3, (void *)i);

    for (int i = 0; i < thread_count; i++)
        pthread_join(threads[i], NULL);

    return 0;
}
