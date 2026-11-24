# Domains to CIDR

Resolve hostnames to IPv4 addresses and aggregate the results into exact CIDR ranges and distinct /24 networks.

## Contents
- `domains.txt`: input hostnames
- `resolve-domains.py`: resolves **A records only** and writes unique IPv4 addresses to `ips.txt`
- `aggregate-cidrs.py`: generates exact CIDR ranges and unique containing /24 networks from `ips.txt`
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

## Generate CIDRs and /24 networks after resolution finishes
```bash
python3 aggregate-cidrs.py
cat cidrs.txt
cat networks-24.txt
```

## Output files
- `ips.txt`: unique resolved IPv4 addresses only
- `cidrs.txt`: exact aggregated IPv4 CIDR ranges (minimal covering ranges)
- `networks-24.txt`: unique /24 network containing each resolved IPv4 address
- `resolve.log`: progress log
- `nohup.out`: process stdout/stderr
- `failed-domains.txt`: domains with no resolved IPv4 addresses

The /24 output is deduplicated and sorted by network address. For example,
`192.0.2.10` and `192.0.2.200` both map to `192.0.2.0/24`, which appears
only once in `networks-24.txt`. The exact CIDR aggregation in `cidrs.txt`
remains independent and unchanged.

Both CIDR outputs are derived only from addresses present in `ips.txt`.
DNS results are a point-in-time snapshot and may change.
