#!/usr/bin/env python3
"""Verify the complete Patch Notes public site after an approved deployment."""

from argparse import ArgumentParser
from html.parser import HTMLParser
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

DEFAULT_BASE = "https://sethusehitch.github.io/patch-notes-society/"
MEDIUM_URL = "https://medium.com/@sethsaper/how-we-got-here-and-how-we-build-a-better-prison-system-ec8f28865dd8"
SUBSTACK_SIGNUP_URL = "https://sethsaperstein.substack.com/subscribe"
ISSUES = [
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
EXPERT_ROUTES = [
    "expert/001-prisons-reviewer-bundle.html",
    "expert/002-housing-homelessness-reviewer-bundle.html",
    *[f"expert/{slug}-reviewer-bundle.html" for slug in ISSUES[2:]],
]


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []
        self.html_lang = None
        self.has_viewport = False
        self.h1_count = 0
        self.main_count = 0
        self.images_missing_alt = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html":
            self.html_lang = attrs.get("lang")
        elif tag == "meta" and attrs.get("name") == "viewport":
            self.has_viewport = True
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "main":
            self.main_count += 1
        elif tag == "img" and "alt" not in attrs:
            self.images_missing_alt.append(attrs.get("src", "<unknown>"))
        elif tag == "a" and attrs.get("href"):
            self.hrefs.append(attrs["href"])


def fail(message):
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def fetch(url, expected_type=None):
    request = urllib.request.Request(url, headers={"User-Agent": "PatchNotesLaunchVerifier/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            status = response.status
            content_type = response.headers.get_content_type()
            body = response.read()
            final_url = response.geturl()
    except (urllib.error.URLError, TimeoutError) as error:
        fail(f"request failed for {url}: {error}")
    if status != 200:
        fail(f"{url} returned HTTP {status}")
    if expected_type:
        expected_types = {expected_type} if isinstance(expected_type, str) else set(expected_type)
        if content_type not in expected_types:
            fail(f"{url} returned {content_type}, expected one of {sorted(expected_types)}")
    return body, final_url


def require(text, token, route):
    if token not in text:
        fail(f"{route} missing expected content: {token}")


def verify_html(base, route, required=()):
    url = urllib.parse.urljoin(base, route)
    body, _ = fetch(url, "text/html")
    text = body.decode("utf-8")
    parsed = LinkParser()
    parsed.feed(text)
    if parsed.html_lang != "en":
        fail(f"{route or '/'} must declare html lang=en")
    if not parsed.has_viewport:
        fail(f"{route or '/'} missing responsive viewport metadata")
    if parsed.h1_count != 1:
        fail(f"{route or '/'} must contain exactly one h1; found {parsed.h1_count}")
    if parsed.main_count != 1:
        fail(f"{route or '/'} must contain exactly one main landmark; found {parsed.main_count}")
    if parsed.images_missing_alt:
        fail(f"{route or '/'} images missing alt text: {parsed.images_missing_alt}")
    for token in required:
        require(text, token, route or "/")
    return text, parsed.hrefs


def verify_external(url):
    _, final_url = fetch(url)
    if url == MEDIUM_URL and not final_url.startswith("https://medium.com/"):
        fail(f"external URL redirected outside expected provider: {url} -> {final_url}")
    if url == SUBSTACK_SIGNUP_URL and not final_url.startswith("https://sethsaperstein.substack.com/"):
        fail(f"external URL redirected outside expected provider: {url} -> {final_url}")


def verify_link_set(base, page_links, check_external):
    internal = set()
    external = set()
    base_parts = urllib.parse.urlsplit(base)
    base_path = base_parts.path.rstrip("/") + "/"
    for page_url, hrefs in page_links.items():
        for href in hrefs:
            if href.startswith(("mailto:", "tel:", "javascript:")) or href == "#":
                continue
            target, _ = urllib.parse.urldefrag(urllib.parse.urljoin(page_url, href))
            parts = urllib.parse.urlsplit(target)
            if parts.scheme not in {"http", "https"}:
                fail(f"unsupported public link scheme: {page_url} -> {href}")
            if parts.netloc == base_parts.netloc and parts.path.startswith(base_path):
                internal.add(target)
            else:
                external.add(target)

    for url in sorted(internal):
        fetch(url)
    if check_external:
        for url in sorted(external):
            verify_external(url)
    return len(internal), len(external)


def main():
    parser = ArgumentParser()
    parser.add_argument("--base-url", default=DEFAULT_BASE)
    parser.add_argument("--check-external", action="store_true")
    args = parser.parse_args()
    base = args.base_url.rstrip("/") + "/"

    page_links = {}
    index, page_links[base] = verify_html(
        base,
        "",
        required=(MEDIUM_URL, "Live on Medium", "Medium essay coming soon", "subscribe.html"),
    )
    if index.count("Medium essay coming soon") != 9:
        fail("index must contain exactly nine Medium essay coming soon labels")

    _, page_links[urllib.parse.urljoin(base, "subscribe.html")] = verify_html(
        base, "subscribe.html", required=(SUBSTACK_SIGNUP_URL, "Subscribe on Substack")
    )
    for route in ["share.html", "review-queue.html", "evidence.html", *EXPERT_ROUTES]:
        _, page_links[urllib.parse.urljoin(base, route)] = verify_html(base, route)
    for slug in ISSUES:
        route = f"issues/{slug}.html"
        _, page_links[urllib.parse.urljoin(base, route)] = verify_html(base, route)

    feed_body, _ = fetch(
        urllib.parse.urljoin(base, "feed.xml"),
        {"application/rss+xml", "application/xml", "text/xml"},
    )
    feed_root = ET.fromstring(feed_body)
    if feed_root.find("channel") is None or not feed_root.findall("channel/item"):
        fail("live feed.xml has no RSS channel/item")

    sitemap_body, _ = fetch(urllib.parse.urljoin(base, "sitemap.xml"))
    sitemap_root = ET.fromstring(sitemap_body)
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    live_locations = {node.text.strip() for node in sitemap_root.findall("sm:url/sm:loc", namespace)}
    required_locations = {
        urllib.parse.urljoin(DEFAULT_BASE, route)
        for route in ["", "subscribe.html", "feed.xml", *EXPERT_ROUTES, *[f"issues/{slug}.html" for slug in ISSUES]]
    }
    missing = sorted(required_locations - live_locations)
    if missing:
        fail(f"live sitemap missing required URLs: {missing}")

    internal_count, external_count = verify_link_set(base, page_links, args.check_external)

    external_status = "checked" if args.check_external else "inventoried"
    print(
        f"public launch live verification ok: {base}; "
        f"internal links checked={internal_count}; external links {external_status}={external_count}"
    )


if __name__ == "__main__":
    main()
