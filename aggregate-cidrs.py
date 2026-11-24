#!/usr/bin/env python3
"""Aggregate IPv4 addresses from ips.txt into exact, minimal CIDR ranges."""
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
            address = ipaddress.ip_address(value)
            if address.version != 4:
                invalid.append((line_number, value, "IPv6 is not supported"))
                continue
            ips.add(address)
        except ValueError:
            invalid.append((line_number, value, "invalid IP address"))

    networks = list(ipaddress.collapse_addresses(ips))
    networks.sort(key=lambda net: int(net.network_address))

    OUTPUT.write_text(
        "".join(f"{network}\n" for network in networks),
        encoding="utf-8"
    )

    print(f"Unique IPv4 addresses: {len(ips)}")
    print(f"CIDR ranges: {len(networks)}")
    print(f"Saved: {OUTPUT}")

    if invalid:
        print(f"Skipped invalid/IPv6 entries: {len(invalid)}", file=sys.stderr)
        for line_number, value, reason in invalid:
            print(f"Line {line_number}: {value} ({reason})", file=sys.stderr)


if __name__ == "__main__":
    main()
