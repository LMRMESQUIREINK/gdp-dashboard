/* canary.c -- a deliberately buggy C program used to prove that the
 * verifier in this build genuinely detects crashes rather than trusting
 * a claim about them. Byte 0 of the input file picks the parser.
 *
 * parse_alpha: heap-buffer-overflow (8-byte buffer, attacker-controlled
 * copy length). The __asm__ volatile barrier is not decoration -- without
 * it, gcc -O1 proves `buf` is never read after the copy and deletes the
 * memcpy as a dead store, so the bug silently stops firing. Verified by
 * hand in this build (see README) before relying on it.
 *
 * parse_bravo: heap-use-after-free (freed on a sentinel id byte, then
 * written through the same pointer).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void parse_alpha(const unsigned char *data, size_t n) {
    if (n < 1) return;
    size_t claimed = data[0];
    char *buf = (char *)malloc(8);
    memcpy(buf, data, claimed);
    __asm__ volatile("" : : "r"(buf) : "memory");
    printf("alpha copied %zu bytes\n", claimed);
    free(buf);
}

struct rec { unsigned char id; unsigned char value; };

static void parse_bravo(const unsigned char *data, size_t n) {
    if (n < 1) return;
    struct rec *r = (struct rec *)malloc(sizeof(struct rec));
    r->id = data[0];
    if (r->id == 0xff) {
        free(r);
    }
    r->value = (n > 1) ? data[1] : 0;
    printf("bravo id=%u value=%u\n", r->id, r->value);
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: %s <input-file>\n", argv[0]);
        return 2;
    }
    FILE *f = fopen(argv[1], "rb");
    if (!f) {
        fprintf(stderr, "cannot open %s\n", argv[1]);
        return 2;
    }
    unsigned char buf[4096];
    size_t n = fread(buf, 1, sizeof(buf), f);
    fclose(f);
    if (n < 1) return 0;

    switch (buf[0]) {
        case 'A': parse_alpha(buf + 1, n - 1); break;
        case 'B': parse_bravo(buf + 1, n - 1); break;
        default:  printf("no parser for byte 0x%02x\n", buf[0]); break;
    }
    return 0;
}
