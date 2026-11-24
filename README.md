# Domains to CIDR

Resolve hostnames to IPv4 addresses and aggregate the results into exact CIDR ranges.

## Contents
- `domains.txt`: input hostnames
- `resolve-domains.py`: resolves **A records only** and writes unique IPv4 addresses to `ips.txt`
- `aggregate-cidrs.py`: aggregates IPv4 addresses from `ips.txt` into CIDR ranges
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

## Monitor
```bash
tail -f resolve.log
# or
tail -f nohup.out
```

The resolver uses `getent ahostsv4` only. It does not query AAAA records
or collect IPv6 addresses. Each lookup has a hard subprocess timeout and
one retry. Results are appended to `ips.txt` as domains finish.
Re-running `run.sh` is refused while the recorded resolver PID is running.

## Generate CIDRs after resolution finishes
```bash
python3 aggregate-cidrs.py
cat cidrs.txt
```

## Output files
- `ips.txt`: unique resolved IPv4 addresses only
- `cidrs.txt`: exact aggregated IPv4 CIDR ranges
- `resolve.log`: progress log
- `nohup.out`: process stdout/stderr
- `failed-domains.txt`: domains with no resolved IPv4 addresses

The CIDR aggregation does not include addresses absent from `ips.txt`.
DNS results are a point-in-time snapshot and may change.
