# DevOps Python Lab

Python utilities for log analysis, cloud inventory patterns, and GitHub API reporting — with pytest, ruff, and GitHub Actions CI.

## Project layout

```
src/
  log_analyzer.py      # CLI Apache log analyzer
  azure_inventory.py   # Azure CLI subprocess inventory stub
  github_report.py     # GitHub REST API reporter
tests/
  test_log_analyzer.py
pyproject.toml         # pytest + ruff configuration
.github/workflows/ci.yml
commit_plan.json
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Usage

### Log analyzer

```bash
python src/log_analyzer.py access.log --top 5
python src/log_analyzer.py access.log --status 404 --json
```

### Azure inventory (requires `az` CLI + auth)

```bash
python src/azure_inventory.py --dry-run
python src/azure_inventory.py -g my-rg -t Microsoft.Compute/virtualMachines
```

### GitHub report (optional token for higher rate limits)

```bash
export GITHUB_TOKEN=ghp_xxx   # never commit real tokens
python src/github_report.py octocat Hello-World
```
