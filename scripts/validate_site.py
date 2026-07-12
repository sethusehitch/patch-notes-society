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
SOURCE_WRAP_ISSUES = {
    "002-housing",
    "003-healthcare",
    "004-education",
    "006-money-politics",
    "008-climate-energy",
    "009-cost-living",
}
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


class AccessibilityParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.html_lang = None
        self.h1_count = 0
        self.main_count = 0
        self.image_errors = []
        self.control_errors = []
        self.label_targets = set()
        self.controls = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html":
            self.html_lang = attrs.get("lang")
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "main":
            self.main_count += 1
        elif tag == "img" and "alt" not in attrs:
            self.image_errors.append(attrs.get("src", "<unknown>"))
        elif tag == "label" and attrs.get("for"):
            self.label_targets.add(attrs["for"])
        elif tag in {"input", "select", "textarea"}:
            if tag == "input" and attrs.get("type", "text") == "hidden":
                return
            self.controls.append((tag, attrs))
        elif tag == "button" and not (attrs.get("aria-label") or attrs.get("title")):
            # Text button names are checked by browser accessibility tooling after deploy.
            pass

    def finish(self):
        for tag, attrs in self.controls:
            control_id = attrs.get("id")
            if not (
                attrs.get("aria-label")
                or attrs.get("aria-labelledby")
                or (control_id and control_id in self.label_targets)
            ):
                self.control_errors.append(f"{tag}#{control_id or '<no-id>'}")


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

    accessibility = AccessibilityParser()
    accessibility.feed(text)
    accessibility.finish()
    if accessibility.html_lang != "en":
        fail(f"{path} must declare html lang=en")
    if '<meta name="viewport"' not in text:
        fail(f"{path} missing responsive viewport metadata")
    if accessibility.h1_count != 1:
        fail(f"{path} must contain exactly one h1; found {accessibility.h1_count}")
    if accessibility.main_count != 1:
        fail(f"{path} must contain exactly one main landmark; found {accessibility.main_count}")
    if accessibility.image_errors:
        fail(f"{path} images missing alt text: {accessibility.image_errors}")
    if accessibility.control_errors:
        fail(f"{path} form controls missing accessible names: {accessibility.control_errors}")


def validate_public_text(path):
    text = read(path)
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in text:
            fail(f"{path} contains forbidden marker: {pattern}")


def validate_signup_route():
    text = read("subscribe.html")
    expected = 'href="https://sethsaperstein.substack.com/subscribe"'
    if expected not in text:
        fail("subscribe.html missing hosted personal Substack signup route")
    if "Confirm by email" in text:
        fail("subscribe.html still presents manual email as the primary signup workflow")


def validate_xml(path):
    ET.parse(ROOT / path)


def validate_feed():
    root = ET.parse(ROOT / "feed.xml").getroot()
    channel = root.find("channel")
    if channel is None:
        fail("feed.xml missing RSS channel")
    for field in ["title", "link", "description", "language", "lastBuildDate"]:
        value = channel.findtext(field, default="").strip()
        if not value:
            fail(f"feed.xml channel missing {field}")
    items = channel.findall("item")
    if not items:
        fail("feed.xml must contain at least one published item")
    seen_guids = set()
    for index, item in enumerate(items, start=1):
        for field in ["title", "link", "description", "guid", "pubDate"]:
            value = item.findtext(field, default="").strip()
            if not value:
                fail(f"feed.xml item {index} missing {field}")
        guid = item.findtext("guid").strip()
        if guid in seen_guids:
            fail(f"feed.xml duplicate item guid: {guid}")
        seen_guids.add(guid)


def validate_sitemap():
    root = ET.parse(ROOT / "sitemap.xml").getroot()
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locations = [node.text.strip() for node in root.findall("sm:url/sm:loc", namespace) if node.text]
    if not locations:
        fail("sitemap.xml contains no URLs")
    if len(locations) != len(set(locations)):
        fail("sitemap.xml contains duplicate URLs")
    for location in locations:
        if not location.startswith(SITE):
            fail(f"sitemap.xml URL is outside canonical site root: {location}")


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
    html_paths = ["index.html", "subscribe.html", "share.html", "review-queue.html", "evidence.html", "expert/001-prisons-reviewer-bundle.html", "expert/002-housing-homelessness-reviewer-bundle.html", "expert/003-healthcare-reviewer-bundle.html", "expert/004-education-reviewer-bundle.html", "expert/005-addiction-mental-health-reviewer-bundle.html", "expert/006-money-politics-reviewer-bundle.html", "expert/007-immigration-reviewer-bundle.html", "expert/008-climate-energy-reviewer-bundle.html", "expert/009-cost-living-reviewer-bundle.html", "expert/010-gun-violence-reviewer-bundle.html"] + [f"issues/{issue}.html" for issue in REQUIRED_ISSUES]
    for path in html_paths:
        if not (ROOT / path).exists():
            fail(f"missing required page {path}")
        validate_html(path)
        validate_local_links(path)
        validate_public_text(path)
    validate_signup_route()

    for path in [".nojekyll", "README.md", "CONTRIBUTING.md", "TRIAGE.md", "llms.txt", "robots.txt", "feed.xml", "sitemap.xml", "scripts/verify_public_launch_live.py", "scripts/verify_remaining_reviewer_bundles_live.py", "scripts/preflight_remaining_reviewer_bundles_publish.py", "scripts/publish_remaining_reviewer_bundles_after_approval.py"]:
        if not (ROOT / path).exists():
            fail(f"missing required file {path}")
        validate_public_text(path)

    for issue in REQUIRED_ISSUES:
        if issue in SOURCE_WRAP_ISSUES and "li{overflow-wrap:anywhere}" not in read(f"issues/{issue}.html"):
            fail(f"issues/{issue}.html missing source-list overflow protection")
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
    validate_feed()
    validate_sitemap()

    sitemap = read("sitemap.xml")
    for url in [SITE, SITE + "subscribe.html", SITE + "share.html", SITE + "review-queue.html", SITE + "evidence.html", SITE + "expert/001-prisons-reviewer-bundle.html", SITE + "expert/002-housing-homelessness-reviewer-bundle.html", SITE + "expert/003-healthcare-reviewer-bundle.html", SITE + "expert/004-education-reviewer-bundle.html", SITE + "expert/005-addiction-mental-health-reviewer-bundle.html", SITE + "expert/006-money-politics-reviewer-bundle.html", SITE + "expert/007-immigration-reviewer-bundle.html", SITE + "expert/008-climate-energy-reviewer-bundle.html", SITE + "expert/009-cost-living-reviewer-bundle.html", SITE + "expert/010-gun-violence-reviewer-bundle.html", SITE + "feed.xml", SITE + "llms.txt"]:
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
