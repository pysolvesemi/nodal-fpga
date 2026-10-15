/* Evidence helper in the same boundary, then execs the actual prebuilt reader. */
#define _GNU_SOURCE
#include <dirent.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <unistd.h>
extern char **environ;
int main(int argc, char **argv) {
    if (argc == 2 && strcmp(argv[1], "--x32") == 0) {
        syscall(0x40000000); /* The filter must kill this ABI attempt. */
        return 90;
    }
    const char *absent[] = {"/usr", "/home", "/workspace", "/bin/sh", "/bin/java",
        "/bin/rustc", "/bin/cargo", "/bin/scala", "/bin/sbt", "/opt"};
    for (size_t i = 0; i < sizeof(absent) / sizeof(absent[0]); ++i) {
        if (access(absent[i], F_OK) == 0) return 11;
    }
    for (char **e = environ; *e != NULL; ++e) {
        if (strcmp(*e, "PATH=/bin") != 0 && strcmp(*e, "LANG=C") != 0 && strcmp(*e, "PWD=/tmp") != 0 && strcmp(*e, "LD_DEBUG=files") != 0) {
            fprintf(stderr, "unexpected runtime environment: %s\n", *e);
            return 12;
        }
    }
    DIR *fds = opendir("/proc/self/fd");
    if (fds == NULL) return 13;
    int ownfd = dirfd(fds);
    struct dirent *entry;
    while ((entry = readdir(fds)) != NULL) {
        char *end;
        long fd = strtol(entry->d_name, &end, 10);
        if (*end == '\0' && fd > 2 && fd != ownfd) return 14;
    }
    closedir(fds);
    for (int fd = 0; fd <= 2; ++fd) {
        struct stat s;
        if (fstat(fd, &s) != 0 || S_ISSOCK(s.st_mode)) return 15;
    }
    if (socket(AF_INET, SOCK_STREAM, 0) != -1 || errno != EPERM) return 16;
    if (socket(AF_INET6, SOCK_STREAM, 0) != -1 || errno != EPERM) return 17;
    int pair[2];
    if (socketpair(AF_UNIX, SOCK_STREAM, 0, pair) != -1 || errno != EPERM) return 18;
    if (syscall(SYS_io_uring_setup, 1, NULL) != -1 || errno != EPERM) return 19;
    long child = syscall(SYS_fork);
    if (child == 0) _exit(92);
    if (child > 0) { waitpid((pid_t)child, NULL, 0); return 22; }
    if (errno != EPERM) return 22;
    /* libc's vfork trampoline preserves the parent's shared stack correctly. */
    pid_t vchild = vfork();
    if (vchild == 0) _exit(93);
    if (vchild > 0) { waitpid(vchild, NULL, 0); return 23; }
    if (errno != EPERM) return 23;
    child = syscall(SYS_clone, 0, NULL, NULL, NULL, 0);
    if (child == 0) _exit(94);
    if (child > 0) { waitpid((pid_t)child, NULL, __WALL); return 24; }
    if (errno != EPERM) return 24;
    if (syscall(SYS_clone3, NULL, 0) != -1 || errno != EPERM) return 25;
    fprintf(stderr, "NF-RUNTIME-POLICY: tool-free root; descriptors=0,1,2; socket4/socket6/socketpair/io_uring/fork/vfork/clone/clone3=EPERM; no network-namespace claim\n");
    if (argc < 2) return 20;
    execv(argv[1], argv + 1);
    perror("exec actual reader");
    return 21;
}
