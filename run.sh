#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

command -v python3 >/dev/null 2>&1 || {
    echo "Error: python3 is required." >&2
    exit 1
}
command -v getent >/dev/null 2>&1 || {
    echo "Error: getent is required (usually provided by libc-bin)." >&2
    exit 1
}

chmod +x resolve-domains.py aggregate-cidrs.py extract-domains.py

if [[ -f resolve.pid ]] && kill -0 "$(cat resolve.pid)" 2>/dev/null; then
    echo "Resolver is already running with PID $(cat resolve.pid)." >&2
    exit 1
fi

python3 extract-domains.py

nohup python3 -u resolve-domains.py > nohup.out 2>&1 &
echo $! > resolve.pid

echo "Started DNS resolver (PID $(cat resolve.pid))."
echo "Monitor: tail -f resolve.log"
echo "Check:   ps -p \"$(cat resolve.pid)\" -o pid,etime,cmd"
echo "After completion: python3 aggregate-cidrs.py"
