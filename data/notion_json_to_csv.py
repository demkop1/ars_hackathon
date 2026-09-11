"""Split notion_export.json into one CSV per database.

The export's top-level keys (locations, calendar, contacts, projects) are
each a flat list of Notion records -- this just writes each one out as its
own CSV, named after the database. List-valued fields (the "Linked *"
relation columns) are joined with "; " since CSV has no native list type;
split back on that delimiter if you need the individual canonical_ids.

Usage: python notion_json_to_csv.py
Reads notion_export.json next to this script, writes to ./notion_export_csv/.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

SOURCE = Path(__file__).parent / "notion_export.json"
OUT_DIR = Path(__file__).parent / "notion_export_csv"
LIST_SEP = "; "


def flatten(value):
    if isinstance(value, list):
        return LIST_SEP.join(str(v) for v in value)
    if value is None:
        return ""
    return value


def write_csv(records: list[dict], path: Path) -> None:
    # union of all keys, in first-seen order, so records with sparse/extra
    # fields (Notion databases are schemaless per-row) don't break the write
    fieldnames: list[str] = []
    seen = set()
    for record in records:
        for key in record:
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow({k: flatten(v) for k, v in record.items()})


def main() -> None:
    with open(SOURCE, encoding="utf-8") as f:
        export = json.load(f)

    databases = export["_meta"]["databases"]
    OUT_DIR.mkdir(exist_ok=True)

    for name in databases:
        records = export[name]
        out_path = OUT_DIR / f"{name}.csv"
        write_csv(records, out_path)
        print(f"{name}: {len(records)} records -> {out_path}")


if __name__ == "__main__":
    main()
