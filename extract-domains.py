#!/usr/bin/env python3
"""Extract distinct hostnames from urls.txt and merge them into domains.txt.

Each URL host is added as both "host" and "www.host". Lines that are not
http(s) URLs with a hostname are skipped. Existing domains.txt entries are kept.
"""
from pathlib import Path
from urllib.parse import urlsplit
import ipaddress
import sys

BASE = Path(__file__).resolve().parent
INPUT = BASE / "urls.txt"
OUTPUT = BASE / "domains.txt"


def hostname_from_url(value):
    parts = urlsplit(value)
    if parts.scheme not in ("http", "https"):
        return None
    host = parts.hostname
    if not host or "." not in host:
        return None
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return host
    return None


def main():
    if not INPUT.exists():
        print(f"{INPUT.name} not found; skipping URL extraction.")
        return

    hosts = {}
    invalid = []

    for line_number, line in enumerate(INPUT.read_text(encoding="utf-8").splitlines(), 1):
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        host = hostname_from_url(value)
        if host is None:
            invalid.append((line_number, value))
            continue
        base = host[4:] if host.startswith("www.") else host
        hosts[base] = None
        hosts[f"www.{base}"] = None

    existing = []
    if OUTPUT.exists():
        existing = [
            line.strip()
            for line in OUTPUT.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
    existing = list(dict.fromkeys(existing))
    existing_set = set(existing)

    new_domains = sorted(domain for domain in hosts if domain not in existing_set)
    domains = existing + new_domains

    OUTPUT.write_text("".join(f"{domain}\n" for domain in domains), encoding="utf-8")

    print(f"Hosts from {INPUT.name}: {len(hosts)} (with www. variants)")
    print(f"New domains added: {len(new_domains)}")
    print(f"Total in {OUTPUT.name}: {len(domains)}")

    if invalid:
        print("\nSkipped non-URL lines:", file=sys.stderr)
        for line_number, value in invalid:
            print(f"Line {line_number}: {value}", file=sys.stderr)


if __name__ == "__main__":
    main()
