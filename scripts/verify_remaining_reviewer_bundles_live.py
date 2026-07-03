#!/usr/bin/env python3
"""Verify that the #006-#010 reviewer bundles are live after Pages deploy."""

from __future__ import annotations

import sys
import urllib.error
import urllib.request


BASE = "https://sethusehitch.github.io/patch-notes-society/"

PATHS = [
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
]

INDEX_EXPECTED = [
    'href="expert/006-money-politics-reviewer-bundle.html"',
    'href="expert/007-immigration-reviewer-bundle.html"',
    'href="expert/008-climate-energy-reviewer-bundle.html"',
    'href="expert/009-cost-living-reviewer-bundle.html"',
    'href="expert/010-gun-violence-reviewer-bundle.html"',
]


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "patch-notes-site-verifier/0.1"})
    with urllib.request.urlopen(request, timeout=20) as response:
        if response.status != 200:
            raise RuntimeError(f"{url} returned HTTP {response.status}")
        return response.read().decode("utf-8", errors="replace")


def main() -> int:
    failures: list[str] = []
    for path in PATHS:
        url = BASE + path
        try:
            body = fetch(url)
            if len(body.strip()) < 200:
                failures.append(f"{url} returned a suspiciously small body")
        except (RuntimeError, urllib.error.URLError, TimeoutError) as exc:
            failures.append(f"{url}: {exc}")

    try:
        index = fetch(BASE)
        for marker in INDEX_EXPECTED:
            if marker not in index:
                failures.append(f"homepage missing {marker}")
    except (RuntimeError, urllib.error.URLError, TimeoutError) as exc:
        failures.append(f"{BASE}: {exc}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1

    print("remaining reviewer bundles live verification ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
