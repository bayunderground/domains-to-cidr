# Domains to CIDR

## Contents
- `domains.txt`: input hostnames
- `resolve-domains.py`: resolves A and AAAA records into unique IPs
- `aggregate-cidrs.py`: aggregates `ips.txt` into exact CIDR ranges
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

The resolver uses `getent ahostsv4` and `getent ahostsv6`, with a hard
subprocess timeout for each lookup and one retry. Results are appended to
`ips.txt` as domains finish. Re-running `run.sh` is refused while the recorded
resolver PID is still running.

## Generate CIDRs after resolution finishes
```bash
python3 aggregate-cidrs.py
cat cidrs.txt
```

## Output files
- `ips.txt`: unique resolved IPv4 and IPv6 addresses
- `cidrs.txt`: exact aggregated CIDR ranges
- `resolve.log`: progress log
- `nohup.out`: process stdout/stderr
- `failed-domains.txt`: domains with no resolved addresses

CIDR aggregation does not include addresses absent from `ips.txt`. DNS results
are a point-in-time snapshot and may change.
