# Domains to CIDR

Русская версия: [README_RU.md](README_RU.md)

## Contents
- `*.har`: Chrome DevTools network exports, top level of the project folder. Converted to `urls.txt` and deleted by `run.sh`
- `extract-har.py`: replaces `urls.txt` with every request URL from the top-level `.har` files, then deletes each file that was read successfully
- `urls.txt`: input URLs, created from `.har` files and removed after `run.sh` uses it (not in git)
- `extract-domains.py`: merges hostnames from `urls.txt` into `domains.txt`, adding both `host` and `www.host`
- `domains.txt`: input hostnames (not in git, generated from `urls.txt` and/or edited by hand)
- `resolve-domains.py`: resolves A and AAAA records into unique IPs
- `aggregate-cidrs.py`: aggregates `ips.txt` into exact CIDR ranges
- `update-networks.py`: expands IPv4 addresses from `ips.txt` into networks (max /20) and appends new ones to `networks.txt`
- `run.sh`: starts DNS resolution in the background with `nohup`

## Requirements
- Python 3
- `getent` (normally provided by `libc-bin` on Debian/Ubuntu)
- No third-party Python packages and no `pip` required

## Run
```bash
chmod +x run.sh
./run.sh
```

`run.sh` first runs `extract-har.py`. If there are top-level `.har` files, it
replaces `urls.txt` with all their request URLs and deletes each file that was
read. Unreadable `.har` files are kept and reported.

Then `run.sh` runs `extract-domains.py`. Its hosts are merged into
`domains.txt` (existing entries are kept, duplicates removed). Lines that are
not http(s) URLs, and IP-address hosts, are skipped with a warning.

After that, `run.sh` deletes `urls.txt`. Do not keep manual changes in
`urls.txt`; they will be removed on the next run.

Note: the resolver overwrites `ips.txt`. Back up manually added IPs first.

## Monitor
```bash
tail -f resolve.log
# or
tail -f nohup.out
```

The resolver uses `getent ahostsv4` and `getent ahostsv6`, with a hard
subprocess timeout for each lookup and one retry. Results are appended to
`ips.txt` as domains finish. Re-running `run.sh` is refused while the recorded
resolver PID is still running.

## Generate CIDRs after resolution finishes
```bash
python3 aggregate-cidrs.py
cat cidrs.txt
```

## Expand networks
`update-networks.py` groups IPv4 addresses from `ips.txt` into /24s, merges
adjacent /24s into larger blocks, and never makes a block larger than /20.
`run.sh` runs it automatically after the resolver finishes. You can also run it
by hand after editing `ips.txt`:
```bash
python3 update-networks.py
```
`networks.txt` is append-only. New blocks are added after a comment line, and
only address space not already listed is appended. Existing lines are never
removed, even if their IPs were removed from `ips.txt`. IPv6 and invalid lines
are skipped.

## Output files
- `ips.txt`: unique resolved IPv4 and IPv6 addresses
- `networks.txt`: expanded IPv4 networks (max /20), appended by `update-networks.py`
- `cidrs.txt`: exact aggregated CIDR ranges
- `resolve.log`: progress log
- `nohup.out`: process stdout/stderr
- `failed-domains.txt`: domains with no resolved addresses

CIDR aggregation does not include addresses absent from `ips.txt`. DNS results
are a point-in-time snapshot and may change.
