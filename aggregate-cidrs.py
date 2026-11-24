#!/usr/bin/env python3
"""Aggregate IPv4 addresses from ips.txt into exact CIDRs and unique /24 networks."""
from pathlib import Path
import ipaddress
import sys

BASE = Path(__file__).resolve().parent
INPUT = BASE / "ips.txt"
OUTPUT = BASE / "cidrs.txt"
OUTPUT_24 = BASE / "networks-24.txt"


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

    # Preserve the existing exact/minimal CIDR aggregation.
    networks = list(ipaddress.collapse_addresses(ips))
    networks.sort(key=lambda net: int(net.network_address))

    OUTPUT.write_text(
        "".join(f"{network}\n" for network in networks),
        encoding="utf-8"
    )

    # Also list the containing /24 for every resolved IPv4 address.
    # A set removes duplicate networks when several IPs share a subnet.
    networks_24 = {
        ipaddress.ip_network(f"{address}/24", strict=False)
        for address in ips
    }
    sorted_networks_24 = sorted(networks_24, key=lambda net: int(net.network_address))
    OUTPUT_24.write_text(
        "".join(f"{network}\n" for network in sorted_networks_24),
        encoding="utf-8"
    )

    print(f"Unique IPv4 addresses: {len(ips)}")
    print(f"Exact CIDR ranges: {len(networks)}")
    print(f"Unique /24 networks: {len(sorted_networks_24)}")
    print(f"Saved: {OUTPUT}")
    print(f"Saved: {OUTPUT_24}")

    if invalid:
        print(f"Skipped invalid/IPv6 entries: {len(invalid)}", file=sys.stderr)
        for line_number, value, reason in invalid:
            print(f"Line {line_number}: {value} ({reason})", file=sys.stderr)


if __name__ == "__main__":
    main()
