#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://sethusehitch.github.io/patch-notes-society/"
REQUIRED_ISSUES = [
    "001-prisons",
    "002-housing",
    "003-healthcare",
    "004-education",
    "005-addiction-mental-health",
    "006-money-politics",
    "007-immigration",
    "008-climate-energy",
    "009-cost-living",
    "010-gun-violence",
]
FORBIDDEN_PATTERNS = [
    "Hold Before Publication",
    "/Users/sethsaperstein",
    "Approval required",
    "Do not publish",
    "Local publishable draft candidate",
]


def fail(message):
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def validate_html(path):
    text = read(path)
    HTMLParser().feed(text)
    if "<title>" not in text:
        fail(f"{path} missing title")
    if "rel=\"canonical\"" not in text:
        fail(f"{path} missing canonical link")
    if "application/ld+json" not in text:
        fail(f"{path} missing JSON-LD")
    blocks = re.findall(r'<script type="application/ld\+json">\n(.*?)\n</script>', text, re.S)
    if not blocks:
        fail(f"{path} missing parseable JSON-LD block")
    for block in blocks:
        json.loads(block)
    if "assets/social-card.png" not in text:
        fail(f"{path} missing social preview image")
    if "feed.xml" not in text:
        fail(f"{path} missing RSS discovery")
    if "llms.txt" not in text:
        fail(f"{path} missing llms.txt discovery")


def validate_public_text(path):
    text = read(path)
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in text:
            fail(f"{path} contains forbidden marker: {pattern}")


def validate_xml(path):
    ET.parse(ROOT / path)


def validate_local_links(path):
    text = read(path)
    for href in re.findall(r'href="([^"]+)"', text):
        if href.startswith(("http://", "https://", "#", "mailto:")):
            continue
        href = href.split("#", 1)[0]
        if href.startswith("/patch-notes-society/"):
            target = ROOT / href.removeprefix("/patch-notes-society/")
            if not target.exists():
                fail(f"{path} has missing site-root href {href}")
            continue
        target = (ROOT / path).parent / href
        if target.is_dir():
            target = target / "index.html"
        if not target.exists():
            fail(f"{path} has missing local href {href}")


def main():
    html_paths = ["index.html", "share.html", "review-queue.html", "evidence.html", "expert/001-prisons-reviewer-bundle.html", "expert/002-housing-homelessness-reviewer-bundle.html", "expert/003-healthcare-reviewer-bundle.html", "expert/004-education-reviewer-bundle.html", "expert/005-addiction-mental-health-reviewer-bundle.html", "expert/006-money-politics-reviewer-bundle.html", "expert/007-immigration-reviewer-bundle.html", "expert/008-climate-energy-reviewer-bundle.html", "expert/009-cost-living-reviewer-bundle.html", "expert/010-gun-violence-reviewer-bundle.html"] + [f"issues/{issue}.html" for issue in REQUIRED_ISSUES]
    for path in html_paths:
        if not (ROOT / path).exists():
            fail(f"missing required page {path}")
        validate_html(path)
        validate_local_links(path)
        validate_public_text(path)

    for path in [".nojekyll", "README.md", "CONTRIBUTING.md", "TRIAGE.md", "llms.txt", "robots.txt", "feed.xml", "sitemap.xml"]:
        if not (ROOT / path).exists():
            fail(f"missing required file {path}")
        validate_public_text(path)

    for issue in REQUIRED_ISSUES:
        path = f"papers/{issue}.md"
        if not (ROOT / path).exists():
            fail(f"missing required markdown paper {path}")
        validate_public_text(path)
    for path in [
        "expert/001-prisons-policy-memo-v0.1.md",
        "expert/001-prisons-evidence-matrix-v0.1.md",
        "expert/002-housing-homelessness-pre-memo-reviewer-brief-v0.1.md",
        "expert/002-housing-homelessness-evidence-matrix-v0.1.md",
        "expert/002-housing-homelessness-source-appendix-v0.1.md",
        "expert/003-healthcare-pre-memo-reviewer-brief-v0.1.md",
        "expert/003-healthcare-evidence-matrix-v0.1.md",
        "expert/003-healthcare-source-appendix-v0.1.md",
        "expert/004-education-pre-memo-reviewer-brief-v0.1.md",
        "expert/004-education-evidence-matrix-v0.1.md",
        "expert/004-education-source-appendix-v0.1.md",
        "expert/005-addiction-mental-health-pre-memo-reviewer-brief-v0.1.md",
        "expert/005-addiction-mental-health-evidence-matrix-v0.1.md",
        "expert/005-addiction-mental-health-source-appendix-v0.1.md",
        "expert/006-money-politics-pre-memo-reviewer-brief-v0.1.md",
        "expert/006-money-politics-evidence-matrix-v0.1.md",
        "expert/006-money-politics-source-appendix-v0.1.md",
        "expert/007-immigration-pre-memo-reviewer-brief-v0.1.md",
        "expert/007-immigration-evidence-matrix-v0.1.md",
        "expert/007-immigration-source-appendix-v0.1.md",
        "expert/008-climate-energy-pre-memo-reviewer-brief-v0.1.md",
        "expert/008-climate-energy-evidence-matrix-v0.1.md",
        "expert/008-climate-energy-source-appendix-v0.1.md",
        "expert/009-cost-living-pre-memo-reviewer-brief-v0.1.md",
        "expert/009-cost-living-evidence-matrix-v0.1.md",
        "expert/009-cost-living-source-appendix-v0.1.md",
        "expert/010-gun-violence-pre-memo-reviewer-brief-v0.1.md",
        "expert/010-gun-violence-evidence-matrix-v0.1.md",
        "expert/010-gun-violence-source-appendix-v0.1.md",
    ]:
        if not (ROOT / path).exists():
            fail(f"missing required expert artifact {path}")
        validate_public_text(path)

    validate_xml("feed.xml")
    validate_xml("sitemap.xml")

    sitemap = read("sitemap.xml")
    for url in [SITE, SITE + "share.html", SITE + "review-queue.html", SITE + "evidence.html", SITE + "expert/001-prisons-reviewer-bundle.html", SITE + "expert/002-housing-homelessness-reviewer-bundle.html", SITE + "expert/003-healthcare-reviewer-bundle.html", SITE + "expert/004-education-reviewer-bundle.html", SITE + "expert/005-addiction-mental-health-reviewer-bundle.html", SITE + "expert/006-money-politics-reviewer-bundle.html", SITE + "expert/007-immigration-reviewer-bundle.html", SITE + "expert/008-climate-energy-reviewer-bundle.html", SITE + "expert/009-cost-living-reviewer-bundle.html", SITE + "expert/010-gun-violence-reviewer-bundle.html", SITE + "feed.xml", SITE + "llms.txt"]:
        if url not in sitemap:
            fail(f"sitemap missing {url}")
    for issue in REQUIRED_ISSUES:
        url = SITE + f"issues/{issue}.html"
        if url not in sitemap:
            fail(f"sitemap missing {url}")
        paper_url = SITE + f"papers/{issue}.md"
        if paper_url not in sitemap:
            fail(f"sitemap missing {paper_url}")

    robots = read("robots.txt")
    for token in ["Sitemap:", "Feed:", "LLMS:"]:
        if token not in robots:
            fail(f"robots.txt missing {token}")

    llms = read("llms.txt")
    for issue in REQUIRED_ISSUES:
        if f"issues/{issue}.html" not in llms:
            fail(f"llms.txt missing {issue}")
        if f"papers/{issue}.md" not in llms:
            fail(f"llms.txt missing markdown paper {issue}")

    print("site validation ok")


if __name__ == "__main__":
    main()
