"""Tests for log_analyzer module."""

from __future__ import annotations

from pathlib import Path

import pytest

from log_analyzer import analyze, format_report, parse_line


SAMPLE_LOG = """\
127.0.0.1 - - [10/Oct/2023:13:55:36 +0000] "GET /index.html HTTP/1.1" 200 2326
127.0.0.1 - - [10/Oct/2023:13:55:37 +0000] "GET /api HTTP/1.1" 404 123
10.0.0.2 - - [10/Oct/2023:13:55:38 +0000] "POST /api HTTP/1.1" 500 50
"""


def test_parse_line_valid() -> None:
    entry = parse_line(
        '127.0.0.1 - - [10/Oct/2023:13:55:36 +0000] "GET / HTTP/1.1" 200 100'
    )
    assert entry is not None
    assert entry.ip == "127.0.0.1"
    assert entry.status == 200
    assert entry.bytes_sent == 100


def test_parse_line_invalid() -> None:
    assert parse_line("not a log line") is None


def test_analyze_summary(tmp_path: Path) -> None:
    logfile = tmp_path / "access.log"
    logfile.write_text(SAMPLE_LOG, encoding="utf-8")
    summary = analyze(logfile)
    assert summary["total_requests"] == 3
    assert summary["unique_ips"] == 2
    assert summary["total_bytes"] == 2326 + 123 + 50


def test_analyze_status_filter(tmp_path: Path) -> None:
    logfile = tmp_path / "access.log"
    logfile.write_text(SAMPLE_LOG, encoding="utf-8")
    summary = analyze(logfile, status_filter=404)
    assert summary["total_requests"] == 1


def test_format_report_contains_totals(tmp_path: Path) -> None:
    logfile = tmp_path / "access.log"
    logfile.write_text(SAMPLE_LOG, encoding="utf-8")
    text = format_report(analyze(logfile))
    assert "total_requests: 3" in text
    assert "top_paths:" in text
