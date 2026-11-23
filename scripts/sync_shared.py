#!/usr/bin/env python3
"""Sync canonical shared files into self-contained skill folders, or verify parity.

Usage:
  python3 scripts/sync_shared.py          # copy shared/ files into skills/
  python3 scripts/sync_shared.py --check  # fail if any skill copy drifted (CI)
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SHARED_MAPPINGS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "shared/validate_kb.py",
        (
            "skills/repo-kb-lint/scripts/validate_kb.py",
            "skills/repo-kb-author/scripts/validate_kb.py",
        ),
    ),
    (
        "shared/knowledge-debt-contract.md",
        (
            "skills/repo-kb-lint/references/knowledge-debt-contract.md",
            "skills/repo-kb-author/references/knowledge-debt-contract.md",
        ),
    ),
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync or check shared skill assets.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify skill copies match shared/ without writing.",
    )
    args = parser.parse_args()

    drifted: list[str] = []
    for src_rel, targets in SHARED_MAPPINGS:
        src = REPO_ROOT / src_rel
        if not src.exists():
            print(f"ERROR: Missing canonical file {src_rel}", file=sys.stderr)
            return 1
        src_bytes = src.read_bytes()
        for dst_rel in targets:
            dst = REPO_ROOT / dst_rel
            if args.check:
                if not dst.exists() or dst.read_bytes() != src_bytes:
                    drifted.append(f"{dst_rel} != {src_rel}")
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                print(f"Synced {src_rel} -> {dst_rel}")

    if args.check:
        if drifted:
            print("Shared file drift detected! Run `python3 scripts/sync_shared.py`:")
            for item in drifted:
                print(f"  - {item}")
            return 1
        print("All shared skill assets are in sync.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
