#!/usr/bin/env python3
"""Repository developer entrypoint; run without installation or root access."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "tools"))
from nf import main

raise SystemExit(main())
