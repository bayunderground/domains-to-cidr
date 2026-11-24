# Domains to CIDR

Русская версия: [README_RU.md](README_RU.md)

## Contents
- `urls.txt`: input URLs (not in git)
- `extract-domains.py`: merges hostnames from `urls.txt` into `domains.txt`, adding both `host` and `www.host`
- `domains.txt`: input hostnames (not in git, generated from `urls.txt` and/or edited by hand)
- `resolve-domains.py`: resolves A and AAAA records into unique IPs
- `aggregate-cidrs.py`: aggregates `ips.txt` into exact CIDR ranges
- `update-networks.py`: appends new IPv4 /24 networks from `ips.txt` to `networks-24.txt`
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

`run.sh` first runs `extract-domains.py`. If `urls.txt` exists, its hosts are
merged into `domains.txt` (existing entries are kept, duplicates removed).
Lines that are not http(s) URLs, and IP-address hosts, are skipped with a
warning. If `urls.txt` is missing, this step is skipped.

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

## Update /24 networks
Run after editing `ips.txt` (manually or after resolution):
```bash
python3 update-networks.py
```
New IPv4 /24 networks are appended to `networks-24.txt` after a comment line.
Existing lines are never removed. IPv6 and invalid lines are skipped.

## Output files
- `ips.txt`: unique resolved IPv4 and IPv6 addresses
- `networks-24.txt`: IPv4 /24 networks, appended by `update-networks.py`
- `cidrs.txt`: exact aggregated CIDR ranges
- `resolve.log`: progress log
- `nohup.out`: process stdout/stderr
- `failed-domains.txt`: domains with no resolved addresses

CIDR aggregation does not include addresses absent from `ips.txt`. DNS results
are a point-in-time snapshot and may change.
