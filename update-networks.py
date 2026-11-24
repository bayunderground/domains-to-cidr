#!/usr/bin/env python3
"""Append IPv4 /24 networks for new addresses in ips.txt to networks-24.txt.

Existing entries are never rewritten or removed. Each run appends a comment
line followed by only the /24 networks not already listed. IPv6 and invalid
lines in ips.txt are skipped.
"""
from pathlib import Path
import ipaddress
import sys
import time

BASE = Path(__file__).resolve().parent
INPUT = BASE / "ips.txt"
OUTPUT = BASE / "networks-24.txt"


def read_existing(path):
    if not path.exists():
        return set()
    networks = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        networks.add(ipaddress.IPv4Network(value))
    return networks


def main():
    if not INPUT.exists():
        raise SystemExit(f"Missing {INPUT.name}.")

    existing = read_existing(OUTPUT)

    candidates = set()
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
        candidates.add(ipaddress.IPv4Network(f"{address}/24", strict=False))

    new_networks = sorted(candidates - existing, key=lambda net: int(net.network_address))

    if new_networks:
        needs_newline = OUTPUT.exists() and OUTPUT.stat().st_size > 0 and not OUTPUT.read_bytes().endswith(b"\n")
        with OUTPUT.open("a", encoding="utf-8") as stream:
            if needs_newline:
                stream.write("\n")
            stream.write(f"# added {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            for network in new_networks:
                stream.write(f"{network}\n")

    print(f"Existing networks: {len(existing)}")
    print(f"New networks appended: {len(new_networks)}")
    print(f"IPv6 skipped: {skipped_ipv6}")
    print(f"Saved: {OUTPUT}")

    if invalid:
        print("\nSkipped invalid entries:", file=sys.stderr)
        for line_number, value in invalid:
            print(f"Line {line_number}: {value}", file=sys.stderr)


if __name__ == "__main__":
    main()
