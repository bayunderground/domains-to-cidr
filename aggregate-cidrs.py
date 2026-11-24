#!/usr/bin/env python3
"""Aggregate IPs from ips.txt into exact, minimal CIDR ranges."""
from pathlib import Path
import ipaddress
import sys

BASE = Path(__file__).resolve().parent
INPUT = BASE / "ips.txt"
OUTPUT = BASE / "cidrs.txt"


def main():
    if not INPUT.exists():
        raise SystemExit(f"Missing {INPUT.name}; run resolve-domains.py first.")

    ips = set()
    invalid = []

    for line_number, line in enumerate(INPUT.read_text(encoding="utf-8").splitlines(), 1):
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        try:
            ips.add(ipaddress.ip_address(value))
        except ValueError:
            invalid.append((line_number, value))

    networks = []
    for version in (4, 6):
        family_ips = [ip for ip in ips if ip.version == version]
        networks.extend(ipaddress.collapse_addresses(family_ips))

    networks.sort(key=lambda net: (net.version, int(net.network_address)))

    OUTPUT.write_text(
        "".join(f"{network}\n" for network in networks),
        encoding="utf-8"
    )

    print(f"Unique IPs: {len(ips)}")
    print(f"IPv4: {sum(ip.version == 4 for ip in ips)}")
    print(f"IPv6: {sum(ip.version == 6 for ip in ips)}")
    print(f"CIDR ranges: {len(networks)}")
    print(f"Saved: {OUTPUT}")

    if invalid:
        print("\nInvalid entries:", file=sys.stderr)
        for line_number, value in invalid:
            print(f"Line {line_number}: {value}", file=sys.stderr)


if __name__ == "__main__":
    main()
