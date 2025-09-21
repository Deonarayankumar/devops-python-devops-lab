"""Azure resource inventory stub using Azure CLI subprocess pattern."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AzureResource:
    name: str
    resource_type: str
    resource_group: str
    location: str

    @classmethod
    def from_cli_row(cls, row: dict[str, Any]) -> AzureResource:
        return cls(
            name=row.get("name", ""),
            resource_type=row.get("type", ""),
            resource_group=row.get("resourceGroup", ""),
            location=row.get("location", ""),
        )


def require_az_cli() -> str:
    az = shutil.which("az")
    if not az:
        raise RuntimeError("Azure CLI (az) not found in PATH. Install: https://aka.ms/installazurecli")
    return az


def run_az(args: list[str], *, subscription: str | None = None) -> list[dict[str, Any]]:
    az = require_az_cli()
    cmd = [az, "resource", "list", "-o", "json", *args]
    if subscription:
        cmd.extend(["--subscription", subscription])
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"az resource list failed: {proc.stderr.strip()}")
    data = json.loads(proc.stdout or "[]")
    if not isinstance(data, list):
        raise RuntimeError("unexpected az output: expected JSON array")
    return data


def inventory(
    *,
    resource_group: str | None = None,
    resource_type: str | None = None,
    subscription: str | None = None,
) -> list[AzureResource]:
    args: list[str] = []
    if resource_group:
        args.extend(["-g", resource_group])
    if resource_type:
        args.extend(["--resource-type", resource_type])
    rows = run_az(args, subscription=subscription)
    return [AzureResource.from_cli_row(row) for row in rows]


def summarize(resources: list[AzureResource]) -> dict[str, Any]:
    by_type: dict[str, int] = {}
    by_rg: dict[str, int] = {}
    for r in resources:
        by_type[r.resource_type] = by_type.get(r.resource_type, 0) + 1
        by_rg[r.resource_group] = by_rg.get(r.resource_group, 0) + 1
    return {
        "total": len(resources),
        "by_type": dict(sorted(by_type.items())),
        "by_resource_group": dict(sorted(by_rg.items())),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Azure resource inventory via az CLI")
    parser.add_argument("-g", "--resource-group", help="Filter by resource group")
    parser.add_argument("-t", "--resource-type", help="Filter by ARM resource type")
    parser.add_argument("-s", "--subscription", help="Azure subscription ID or name")
    parser.add_argument("--dry-run", action="store_true", help="Print command without calling az")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.dry_run:
        cmd = [
            "az",
            "resource",
            "list",
            "-o",
            "json",
            *(["-g", args.resource_group] if args.resource_group else []),
            *(["--resource-type", args.resource_type] if args.resource_type else []),
            *(["--subscription", args.subscription] if args.subscription else []),
        ]
        print(" ".join(cmd))
        return 0

    try:
        resources = inventory(
            resource_group=args.resource_group,
            resource_type=args.resource_type,
            subscription=args.subscription,
        )
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(summarize(resources), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
