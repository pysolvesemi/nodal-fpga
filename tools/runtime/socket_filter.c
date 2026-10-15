/* Host-side filter generator, not a Rust consumer dependency. Linux x86_64 only.
 * This is scoped socket denial, not a network namespace or hostile-code sandbox.
 * Kill alternate ABIs; deny socket operations and all io_uring entry points.
 */
#include <errno.h>
#include <linux/audit.h>
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <stddef.h>
#include <stdio.h>
#include <sys/syscall.h>
#define DENY(n) BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, (n), 0, 1), \
                BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | EPERM)
int main(void) {
    const struct sock_filter filter[] = {
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, arch)),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_X86_64, 1, 0),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr)),
        BPF_JUMP(BPF_JMP | BPF_JGE | BPF_K, 0x40000000, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        DENY(__NR_socket), DENY(__NR_socketpair), DENY(__NR_connect),
        DENY(__NR_accept), DENY(__NR_accept4), DENY(__NR_bind), DENY(__NR_listen),
        DENY(__NR_sendto), DENY(__NR_recvfrom), DENY(__NR_sendmsg),
        DENY(__NR_recvmsg), DENY(__NR_sendmmsg), DENY(__NR_recvmmsg),
        DENY(__NR_shutdown), DENY(__NR_getsockname), DENY(__NR_getpeername),
        DENY(__NR_setsockopt), DENY(__NR_getsockopt),
        DENY(__NR_io_uring_setup), DENY(__NR_io_uring_enter), DENY(__NR_io_uring_register),
        DENY(__NR_fork), DENY(__NR_vfork), DENY(__NR_clone), DENY(__NR_clone3),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW)
    };
    return fwrite(filter, sizeof(filter), 1, stdout) == 1 ? 0 : 1;
}
