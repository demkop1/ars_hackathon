"""Convert prepared_cards.json into a single flat CSV.

Each record is a flat card (id, title, category, highlight, time,
preview_text, full_desc, embedding_input) plus one nested `location` dict
(venue, area, lat, lng, services). CSV has no nested-object type, so
`location.*` is flattened into `location_venue`, `location_area`, etc.

Usage: python prepared_cards_to_csv.py
Reads prepared_cards.json next to this script, writes prepared_cards.csv.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

SOURCE = Path(__file__).parent / "prepared_cards.json"
OUT_PATH = Path(__file__).parent / "prepared_cards.csv"


def flatten_record(record: dict) -> dict:
    flat = {}
    for key, value in record.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                flat[f"{key}_{sub_key}"] = sub_value
        else:
            flat[key] = value
    return flat


def main() -> None:
    with open(SOURCE, encoding="utf-8") as f:
        records = json.load(f)

    flat_records = [flatten_record(r) for r in records]

    fieldnames: list[str] = []
    seen = set()
    for record in flat_records:
        for key in record:
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)

    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flat_records)

    print(f"{len(flat_records)} records -> {OUT_PATH}")


if __name__ == "__main__":
    main()
