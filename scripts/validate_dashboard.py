#!/usr/bin/env python3
"""Fail fast on dashboard JavaScript or deployment-data contract regressions."""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    match = re.search(r"<script>(.*?)</script>", html, re.DOTALL)
    if not match:
        raise SystemExit("inline dashboard script not found")
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as script:
        script.write(match.group(1))
        script.flush()
        subprocess.run(["node", "--check", script.name], check=True)

    data = json.loads((ROOT / "data.json").read_text(encoding="utf-8"))
    required = {
        "updated_at",
        "generated_at",
        "market_open",
        "market_session",
        "execution_mode",
        "collection_status",
        "account",
        "holdings",
        "watchlist",
    }
    missing = sorted(required - data.keys())
    if missing:
        raise SystemExit(f"data.json missing keys: {', '.join(missing)}")
    if data["execution_mode"] not in {"LIVE", "PAPER"}:
        raise SystemExit("invalid execution_mode")
    if not isinstance(data["watchlist"], list):
        raise SystemExit("watchlist must be an array")
    watchlist_fields = {
        "symbol",
        "strategy",
        "price",
        "entry",
        "stop",
        "target",
        "rr",
        "adv_usd",
        "score",
    }
    for index, row in enumerate(data["watchlist"]):
        missing_row = sorted(watchlist_fields - row.keys())
        if missing_row:
            raise SystemExit(f"watchlist[{index}] missing: {', '.join(missing_row)}")
    if "marketIsOpenNow" not in html or "cache: 'no-store'" not in html:
        raise SystemExit("dashboard must derive live status from session timestamps and bypass stale data cache")
    print(f"dashboard valid: watchlist={len(data['watchlist'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
