"""Small verifier for the exact Linux classic-BPF filter emitted by our C source."""
import struct

DENIED = {41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55,
          288, 299, 307, 425, 426, 427, 56, 57, 58, 435}
KILL = 0x80000000
ERRNO_EPERM = 0x00050001
ALLOW = 0x7fff0000
X86_64 = 0xc000003e


def evaluate(blob, syscall, arch=X86_64):
    if not blob or len(blob) % 8:
        raise ValueError("invalid classic-BPF length")
    instructions = list(struct.iter_unpack("=HBBI", blob))
    pc, accumulator = 0, 0
    for _ in range(len(instructions) + 1):
        if not 0 <= pc < len(instructions):
            raise ValueError("classic-BPF jump escaped program")
        code, yes, no, value = instructions[pc]
        if code == 0x20:
            if value not in {0, 4}:
                raise ValueError("unreviewed seccomp-data offset")
            accumulator = arch if value == 4 else syscall & 0xffffffff
        elif code == 0x15:
            pc += yes if accumulator == value else no
        elif code == 0x35:
            pc += yes if accumulator >= value else no
        elif code == 0x06:
            return value
        else:
            raise ValueError("unreviewed classic-BPF opcode")
        pc += 1
    raise ValueError("classic-BPF did not return")


def verify(blob):
    for syscall in DENIED:
        if evaluate(blob, syscall) != ERRNO_EPERM:
            raise ValueError(f"socket/io_uring/process syscall {syscall} is not denied")
    for syscall in [0, 1, 2, 3, 9, 10, 11, 12, 59, 60, 231, 257]:
        if evaluate(blob, syscall) != ALLOW:
            raise ValueError(f"ordinary runtime syscall {syscall} unexpectedly denied")
    for arch in [0, 0x40000003, 0xc00000b7, 0x8000003e]:
        if evaluate(blob, 0, arch) != KILL:
            raise ValueError("alternate syscall architecture not killed")
    for syscall in [0x40000000, 0x40000001, 0x40000029, 0xffffffff]:
        if evaluate(blob, syscall) != KILL:
            raise ValueError("x32/negative syscall ABI not killed")
