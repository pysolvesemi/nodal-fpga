#!/usr/bin/env bash
set -euo pipefail

# Run as the cloud environment's setup command on Debian or Ubuntu.
if ! command -v apt-get >/dev/null 2>&1; then
  echo 'This setup requires a Debian or Ubuntu environment.' >&2
  exit 1
fi

if [[ "$(id -u)" == 0 ]]; then
  privilege=()
elif command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
  privilege=(sudo -n)
else
  echo 'Setup requires root or passwordless sudo. Run it during environment provisioning.' >&2
  exit 1
fi

"${privilege[@]}" apt-get update
"${privilege[@]}" env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  ca-certificates git build-essential cmake ninja-build pkg-config \
  python3 python3-venv yosys verilator iverilog

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
python3 -m venv "$repo_root/.venv"

yosys -V
verilator --version
iverilog -V
"$repo_root/.venv/bin/python" --version
