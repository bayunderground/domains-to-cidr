#!/usr/bin/env python3
"""Resolve domains.txt to unique IPv4 addresses only (A records)."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import ipaddress
import shutil
import subprocess
import threading
import time

BASE = Path(__file__).resolve().parent
INPUT = BASE / "domains.txt"
OUTPUT = BASE / "ips.txt"
LOG = BASE / "resolve.log"
FAILED = BASE / "failed-domains.txt"

WORKERS = 10
DNS_TIMEOUT = 5       # seconds per lookup
RETRIES = 1
RETRY_DELAY = 0.5

log_lock = threading.Lock()


def log(message):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    with log_lock:
        print(line, flush=True)
        with LOG.open("a", encoding="utf-8") as stream:
            stream.write(line + "\n")


def lookup_ipv4(domain):
    """Resolve A records through getent, enforcing a hard timeout."""
    result = subprocess.run(
        ["getent", "ahostsv4", domain],
        capture_output=True,
        text=True,
        timeout=DNS_TIMEOUT,
        check=False,
    )

    found = set()
    for line in result.stdout.splitlines():
        fields = line.split()
        if not fields:
            continue
        try:
            address = ipaddress.ip_address(fields[0])
        except ValueError:
            continue
        if address.version == 4:
            found.add(str(address))

    return found, result.returncode, result.stderr.strip()


def resolve(domain):
    errors = []

    for attempt in range(RETRIES + 1):
        try:
            addresses, returncode, stderr = lookup_ipv4(domain)
            if addresses or returncode == 2:
                return domain, addresses, errors
            errors.append(f"getent exit={returncode} {stderr}".strip())
        except subprocess.TimeoutExpired:
            errors.append(f"timed out after {DNS_TIMEOUT}s")
        except Exception as exc:
            errors.append(str(exc))

        if attempt < RETRIES:
            time.sleep(RETRY_DELAY)

    return domain, set(), errors


def ip_sort_key(value):
    return int(ipaddress.IPv4Address(value))


def main():
    if shutil.which("getent") is None:
        raise SystemExit("Required command 'getent' was not found (usually provided by libc-bin).")
    if not INPUT.exists():
        raise SystemExit(f"Missing input file: {INPUT}")

    domains = list(dict.fromkeys(
        line.strip()
        for line in INPUT.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ))

    OUTPUT.write_text("", encoding="utf-8")
    LOG.write_text("", encoding="utf-8")
    FAILED.write_text("", encoding="utf-8")

    all_ips = set()
    failed = []
    log(f"Starting IPv4-only A-record resolution: {len(domains)} domains; workers={WORKERS}; timeout={DNS_TIMEOUT}s")

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(resolve, domain) for domain in domains]
        for index, future in enumerate(as_completed(futures), 1):
            domain, ips, errors = future.result()
            new_ips = ips - all_ips
            all_ips.update(ips)

            if new_ips:
                with OUTPUT.open("a", encoding="utf-8") as stream:
                    for address in sorted(new_ips, key=ip_sort_key):
                        stream.write(address + "\n")
                    stream.flush()

            if not ips:
                failed.append(domain)
                detail = "; ".join(errors) if errors else "no A records"
                log(f"[{index}/{len(domains)}] FAILED {domain}: {detail}")
            else:
                log(f"[{index}/{len(domains)}] {domain}: {', '.join(sorted(ips, key=ip_sort_key))}")

    FAILED.write_text("".join(domain + "\n" for domain in failed), encoding="utf-8")
    log(f"Finished. Unique IPv4 addresses={len(all_ips)}; failed domains={len(failed)}")
    log(f"Results: {OUTPUT.name}; failures: {FAILED.name}")


if __name__ == "__main__":
    main()
