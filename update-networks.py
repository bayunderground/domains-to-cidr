#!/usr/bin/env python3
"""Expand IPv4 addresses from ips.txt into networks and append new ones to networks.txt.

Addresses are grouped into /24s, adjacent /24s are merged into larger blocks,
and no block is larger than /20. networks.txt is append-only: existing lines
are never rewritten or removed, and only address space not already covered is
appended, after a comment line. IPv6 and invalid lines are skipped.
"""
from pathlib import Path
import ipaddress
import sys
import time

BASE = Path(__file__).resolve().parent
INPUT = BASE / "ips.txt"
OUTPUT = BASE / "networks.txt"
MAX_PREFIX = 20


def read_existing(path):
    if not path.exists():
        return []
    networks = []
    for line in path.read_text(encoding="utf-8").splitlines():
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        networks.append(ipaddress.IPv4Network(value))
    return networks


def expand(networks):
    expanded = []
    for block in ipaddress.collapse_addresses(networks):
        if block.prefixlen < MAX_PREFIX:
            expanded.extend(block.subnets(new_prefix=MAX_PREFIX))
        else:
            expanded.append(block)
    return expanded


def uncovered(block, existing):
    if any(block.subnet_of(net) for net in existing):
        return []
    if not any(net.overlaps(block) for net in existing):
        return [block]
    result = []
    for half in block.subnets(prefixlen_diff=1):
        result.extend(uncovered(half, existing))
    return result


def main():
    if not INPUT.exists():
        raise SystemExit(f"Missing {INPUT.name}.")

    existing = read_existing(OUTPUT)

    slash24 = set()
    invalid = []
    skipped_ipv6 = 0

    for line_number, line in enumerate(INPUT.read_text(encoding="utf-8").splitlines(), 1):
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        try:
            address = ipaddress.ip_address(value)
        except ValueError:
            invalid.append((line_number, value))
            continue
        if address.version == 6:
            skipped_ipv6 += 1
            continue
        slash24.add(ipaddress.IPv4Network(f"{address}/24", strict=False))

    targets = expand(sorted(slash24, key=lambda net: int(net.network_address)))

    new_networks = []
    for block in targets:
        new_networks.extend(uncovered(block, existing))
    new_networks.sort(key=lambda net: int(net.network_address))

    if new_networks:
        needs_newline = OUTPUT.exists() and OUTPUT.stat().st_size > 0 and not OUTPUT.read_bytes().endswith(b"\n")
        with OUTPUT.open("a", encoding="utf-8") as stream:
            if needs_newline:
                stream.write("\n")
            stream.write(f"# added {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            for network in new_networks:
                stream.write(f"{network}\n")

    print(f"Existing networks: {len(existing)}")
    print(f"Expanded blocks from ips.txt: {len(targets)}")
    print(f"New networks appended: {len(new_networks)}")
    print(f"IPv6 skipped: {skipped_ipv6}")
    print(f"Saved: {OUTPUT}")

    if invalid:
        print("\nSkipped invalid entries:", file=sys.stderr)
        for line_number, value in invalid:
            print(f"Line {line_number}: {value}", file=sys.stderr)


if __name__ == "__main__":
    main()
