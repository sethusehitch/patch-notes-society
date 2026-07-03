#!/usr/bin/env python3
"""Gated publisher for #006-#010 reviewer bundles.

Default mode is dry-run and performs no push.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APPROVAL_PHRASE = "Publish the staged #006, #007, #008, #009, and #010 reviewer bundles to GitHub Pages."


def run(args: list[str]) -> str:
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"{' '.join(args)} failed:\n{result.stderr or result.stdout}")
    output = result.stdout.strip()
    if output:
        print(output)
    return output


def require_approval(execute: bool) -> None:
    supplied = os.environ.get("PATCH_NOTES_APPROVAL_PHRASE", "")
    if not execute:
        print("dry-run mode: no push will be performed")
        print("set --execute and PATCH_NOTES_APPROVAL_PHRASE to publish after approval")
        return
    if supplied != APPROVAL_PHRASE:
        raise RuntimeError(
            "approval phrase missing or incorrect; refusing to push. "
            "Set PATCH_NOTES_APPROVAL_PHRASE to the exact approved phrase."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish #006-#010 reviewer bundles after explicit approval.")
    parser.add_argument("--execute", action="store_true", help="perform git push after approval phrase check")
    args = parser.parse_args()

    try:
        require_approval(args.execute)
        run(["git", "fetch", "origin"])
        run(["git", "status", "--short", "--branch"])
        run(["git", "rev-list", "--left-right", "--count", "origin/main...HEAD"])
        run(["python3", "scripts/preflight_remaining_reviewer_bundles_publish.py"])

        if not args.execute:
            print("DRY RUN: would run `git push origin main` after approval")
            print("DRY RUN: would run live verifier after Pages deploy")
            return 0

        run(["git", "push", "origin", "main"])
        print("push complete; wait for GitHub Pages deploy before running live verifier")
        print("next: python3 scripts/verify_remaining_reviewer_bundles_live.py")
        return 0
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
