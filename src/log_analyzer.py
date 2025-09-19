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


def analyze(path: Path, *, status_filter: int | None = None, top_n: int = 10) -> dict[str, object]:
    entries: list[LogEntry] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        entry = parse_line(line)
        if entry is None:
            continue
        if status_filter is not None and entry.status != status_filter:
            continue
        entries.append(entry)

    path_counts = Counter(e.path for e in entries)
    status_counts = Counter(e.status for e in entries)
    ip_counts = Counter(e.ip for e in entries)

    return {
        "total_requests": len(entries),
        "unique_ips": len(ip_counts),
        "top_paths": path_counts.most_common(top_n),
        "status_codes": dict(sorted(status_counts.items())),
        "total_bytes": sum(e.bytes_sent for e in entries),
    }


def format_report(summary: dict[str, object]) -> str:
    lines = [
        f"total_requests: {summary['total_requests']}",
        f"unique_ips: {summary['unique_ips']}",
        f"total_bytes: {summary['total_bytes']}",
        "status_codes:",
    ]
    for code, count in summary["status_codes"].items():  # type: ignore[union-attr]
        lines.append(f"  {code}: {count}")
    lines.append("top_paths:")
    for path, count in summary["top_paths"]:  # type: ignore[union-attr]
        lines.append(f"  {path} ({count})")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze Apache-style access logs")
    parser.add_argument("logfile", type=Path, help="Path to access log file")
    parser.add_argument("--status", type=int, help="Filter by HTTP status code")
    parser.add_argument("--top", type=int, default=10, help="Top N paths to display")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.logfile.is_file():
        parser.error(f"file not found: {args.logfile}")

    summary = analyze(args.logfile, status_filter=args.status, top_n=args.top)
    if args.json:
        import json

        print(json.dumps(summary, indent=2))
    else:
        print(format_report(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
