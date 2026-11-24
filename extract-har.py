#!/usr/bin/env python3
"""Replace urls.txt with every request URL from the top-level .har files.

Each .har file that is read successfully is deleted after urls.txt is written.
Files that cannot be parsed are kept and reported. If there are no .har files,
urls.txt is left unchanged.
"""
from pathlib import Path
import json
import sys

BASE = Path(__file__).resolve().parent
OUTPUT = BASE / "urls.txt"


def read_urls(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    return [entry["request"]["url"] for entry in data["log"]["entries"]]


def main():
    har_files = sorted(BASE.glob("*.har"))
    if not har_files:
        print("No .har files found; urls.txt unchanged.")
        return

    urls = []
    readable = []
    failed = []

    for path in har_files:
        try:
            urls.extend(read_urls(path))
            readable.append(path)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            failed.append((path, exc))

    if readable:
        distinct = list(dict.fromkeys(url for url in urls if url))
        OUTPUT.write_text("".join(f"{url}\n" for url in distinct), encoding="utf-8")
        print(f"HAR files read: {len(readable)}")
        print(f"Distinct URLs written to {OUTPUT.name}: {len(distinct)}")

        for path in readable:
            path.unlink()
            print(f"Deleted: {path.name}")

    for path, exc in failed:
        print(f"Kept (could not read) {path.name}: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
