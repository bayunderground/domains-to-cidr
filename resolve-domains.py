#!/usr/bin/env python3
"""Resolve domains.txt using the host's getent/NSS resolver.

No third-party Python packages are required. Each A/AAAA lookup is run as
its own subprocess with a hard timeout, so a stuck system resolver cannot
hold a worker forever.
"""
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
DNS_TIMEOUT = 5       # seconds per address-family lookup
RETRIES = 1
RETRY_DELAY = 0.5

log_lock = threading.Lock()


def log(message):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    with log_lock:
        print(line, flush=True)
        with LOG.open("a", encoding="utf-8") as stream:
            stream.write(line + "\n")


def lookup(domain, record_type):
    """Return IP strings from getent; enforce a hard subprocess timeout."""
    command = ["getent", f"ahosts{record_type}", domain]
    result = subprocess.run(
        command,
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
        if address.version == (4 if record_type == "v4" else 6):
            found.add(str(address))
    return found, result.returncode, result.stderr.strip()


def resolve(domain):
    found = set()
    errors = []

    for record_type in ("v4", "v6"):
        for attempt in range(RETRIES + 1):
            try:
                addresses, returncode, stderr = lookup(domain, record_type)
                found.update(addresses)
                if addresses or returncode == 2:
                    # Success, or no records for this family.
                    break
                errors.append(f"{record_type}: getent exit={returncode} {stderr}".strip())
            except subprocess.TimeoutExpired:
                errors.append(f"{record_type}: timed out after {DNS_TIMEOUT}s")
            except Exception as exc:
                errors.append(f"{record_type}: {exc}")

            if attempt < RETRIES:
                time.sleep(RETRY_DELAY)

    return domain, found, errors


def ip_sort_key(value):
    address = ipaddress.ip_address(value)
    return address.version, int(address)


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
    log(f"Starting: {len(domains)} domains; workers={WORKERS}; timeout={DNS_TIMEOUT}s per query")

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
                detail = "; ".join(errors) if errors else "no A/AAAA records"
                log(f"[{index}/{len(domains)}] FAILED {domain}: {detail}")
            else:
                log(f"[{index}/{len(domains)}] {domain}: {', '.join(sorted(ips, key=ip_sort_key))}")

    FAILED.write_text("".join(domain + "\n" for domain in failed), encoding="utf-8")
    log(f"Finished. Unique IPs={len(all_ips)}; failed domains={len(failed)}")
    log(f"Results: {OUTPUT.name}; failures: {FAILED.name}")


if __name__ == "__main__":
    main()
