"""CLI log analyzer for common web server access logs."""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

# Apache combined log format (simplified)
LOG_PATTERN = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ \[(?P<timestamp>[^\]]+)\] '
    r'"(?P<method>\S+) (?P<path>\S+) (?P<protocol>[^"]+)" '
    r'(?P<status>\d{3}) (?P<bytes>\S+)'
)


@dataclass(frozen=True)
class LogEntry:
    ip: str
    timestamp: str
    method: str
    path: str
    status: int
    bytes_sent: int


def parse_line(line: str) -> LogEntry | None:
    match = LOG_PATTERN.match(line.strip())
    if not match:
        return None
    groups = match.groupdict()
    bytes_raw = groups["bytes"]
    bytes_sent = 0 if bytes_raw == "-" else int(bytes_raw)
    return LogEntry(
        ip=groups["ip"],
        timestamp=groups["timestamp"],
        method=groups["method"],
        path=groups["path"],
        status=int(groups["status"]),
        bytes_sent=bytes_sent,
    )


def main():
    print('log analyzer stub')

if __name__ == '__main__':
    main()
