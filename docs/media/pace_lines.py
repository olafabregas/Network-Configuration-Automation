#!/usr/bin/env python3
"""Release a command's stdout line by line so a terminal recording stays readable.

The bytes written here are exactly the bytes read from stdin. Nothing is
added, dropped, or rewritten. Only the timing changes: NetAuto's demo
walkthrough prints every section in one burst, which flashes past on camera.

``docs/media/pace.sh`` pipes ``python netauto.py`` through this filter.
"""

from __future__ import annotations

import os
import re
import select
import sys
import time

_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
_IDLE_FLUSH_SECONDS = 0.05


def delay_for(line: bytes) -> float:
    """Seconds to hold after this complete line is shown."""
    plain = _ANSI.sub("", line.decode("utf-8", "replace")).rstrip("\r")
    if plain.startswith("Loopback0"):
        return 1.9
    if plain.startswith("Success rate"):
        return 1.45
    if plain.startswith("Simulated backup only"):
        return 1.05
    if "is the neighbor" in plain:
        return 0.9
    if plain.startswith("Saved running-config"):
        return 0.8
    if plain.startswith("Interactive menu:"):
        return 0.7
    if plain.startswith("R1#") or plain.startswith("R2#"):
        return 0.6
    if plain.startswith("!!!!!"):
        return 0.45
    if plain.startswith("Walkthrough complete"):
        return 0.45
    if plain.startswith("Sending "):
        return 0.38
    if plain.startswith("Sample:"):
        return 0.42
    if plain.startswith("--- ") or plain.startswith("=== "):
        return 0.34
    if plain.startswith("Interface "):
        return 0.28
    if plain.startswith("GigabitEthernet"):
        return 0.24
    if plain.startswith("Goodbye"):
        return 0.35
    if not plain.strip():
        return 0.05
    return 0.22


def _write(payload: bytes) -> None:
    sys.stdout.buffer.write(payload)
    sys.stdout.buffer.flush()


def main() -> int:
    if sys.stdin.isatty():
        print(
            "pace_lines.py reads a program's stdout on stdin. "
            "It is invoked by docs/media/pace.sh during a recording.",
            file=sys.stderr,
        )
        return 2

    source = sys.stdin.buffer.fileno()
    pending = b""
    while True:
        readable, _, _ = select.select([source], [], [], _IDLE_FLUSH_SECONDS)
        if not readable:
            if pending:
                _write(pending)
                pending = b""
            continue
        chunk = os.read(source, 65536)
        if not chunk:
            if pending:
                _write(pending)
            return 0
        pending += chunk
        while b"\n" in pending:
            line, pending = pending.split(b"\n", 1)
            _write(line + b"\n")
            time.sleep(delay_for(line))


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        raise SystemExit(0)
