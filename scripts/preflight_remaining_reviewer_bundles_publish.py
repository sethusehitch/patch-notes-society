#!/usr/bin/env python3
"""No-push preflight for publishing #006-#010 reviewer bundles."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NETWORKING = ROOT.parent
EXPECTED_LEFT_RIGHT = "0\t4"
EXPECTED_COMMITS = {
    "0243190": "Add remaining reviewer bundles",
    "7c447e3": "Add live verifier for remaining reviewer bundles",
}

REQUIRED_FILES = [
    "expert/006-money-politics-reviewer-bundle.html",
    "expert/006-money-politics-pre-memo-reviewer-brief-v0.1.md",
    "expert/006-money-politics-evidence-matrix-v0.1.md",
    "expert/006-money-politics-source-appendix-v0.1.md",
    "expert/007-immigration-reviewer-bundle.html",
    "expert/007-immigration-pre-memo-reviewer-brief-v0.1.md",
    "expert/007-immigration-evidence-matrix-v0.1.md",
    "expert/007-immigration-source-appendix-v0.1.md",
    "expert/008-climate-energy-reviewer-bundle.html",
    "expert/008-climate-energy-pre-memo-reviewer-brief-v0.1.md",
    "expert/008-climate-energy-evidence-matrix-v0.1.md",
    "expert/008-climate-energy-source-appendix-v0.1.md",
    "expert/009-cost-living-reviewer-bundle.html",
    "expert/009-cost-living-pre-memo-reviewer-brief-v0.1.md",
    "expert/009-cost-living-evidence-matrix-v0.1.md",
    "expert/009-cost-living-source-appendix-v0.1.md",
    "expert/010-gun-violence-reviewer-bundle.html",
    "expert/010-gun-violence-pre-memo-reviewer-brief-v0.1.md",
    "expert/010-gun-violence-evidence-matrix-v0.1.md",
    "expert/010-gun-violence-source-appendix-v0.1.md",
    "scripts/verify_remaining_reviewer_bundles_live.py",
    "scripts/publish_remaining_reviewer_bundles_after_approval.py",
]

CONTROL_FILES = [
    "patch-notes-staged-reviewer-bundles-publish-approval-packet-v0.1.md",
    "patch-notes-remaining-bundles-go-no-go-card-v0.1.md",
    "patch-notes-remaining-bundles-post-publish-audit-log-template-v0.1.md",
    "patch-notes-remaining-bundles-post-deploy-distribution-packet-v0.1.md",
    "patch-notes-remaining-bundles-post-publish-control-update-checklist-v0.1.md",
    "patch-notes-publishing-approval-manifest.json",
]


def run(args: list[str], cwd: Path = ROOT) -> str:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"{' '.join(args)} failed:\n{result.stderr or result.stdout}")
    return result.stdout.strip()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    try:
        status = run(["git", "status", "--short", "--branch"])
        require(status == "## main...origin/main [ahead 4]", f"unexpected git status: {status}")

        divergence = run(["git", "rev-list", "--left-right", "--count", "origin/main...HEAD"])
        require(divergence == EXPECTED_LEFT_RIGHT, f"unexpected divergence: {divergence}")

        log = run(["git", "log", "--oneline", "--max-count=8"])
        for commit, subject in EXPECTED_COMMITS.items():
            require(f"{commit} {subject}" in log, f"missing expected commit {commit} {subject}")

        for path in REQUIRED_FILES:
            require((ROOT / path).exists(), f"missing required site file {path}")

        for path in CONTROL_FILES:
            require((NETWORKING / path).exists(), f"missing required control file {path}")

        run(["python3", "scripts/validate_site.py"])
        with (NETWORKING / "patch-notes-publishing-approval-manifest.json").open(encoding="utf-8") as f:
            json.load(f)

        print("remaining reviewer bundles publish preflight ok")
        print("no push performed")
        return 0
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
