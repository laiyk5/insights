"""Download city housing price data from cityre.cn API."""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def parse_unit_price(raw: str) -> float:
    """Parse strings like '6.95万' into yuan per sqm."""
    match = re.match(r"([\d.]+)万", raw.strip())
    if match:
        return float(match.group(1)) * 10_000
    # fallback for plain numbers
    return float(raw)


def fetch_city_price_data() -> list[dict]:
    """Fetch housing price data for all cities from cityre.cn."""
    url = "https://www.cityre.cn/target/gethousingPriceList"
    params = {"queryType": "housingPrice"}
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    raw_data = resp.json()

    records = []
    for item in raw_data:
        records.append({
            "city_name": item["cityName"],
            "province_name": item["provinceName"],
            "listing_count": int(item["priceCount"]),
            "price_per_sqm": round(parse_unit_price(item["unitPrice"]), 2),
            "recorded_at": date.today().isoformat(),
        })
    return records


def main():
    data_dir = Path(__file__).resolve().parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    print("Fetching city housing price data from cityre.cn...")
    records = fetch_city_price_data()
    print(f"Fetched {len(records)} cities")

    top10 = sorted(records, key=lambda r: r["price_per_sqm"], reverse=True)[:10]
    print("\nTop 10 most expensive cities (¥/m²):")
    for r in top10:
        print(f"  {r['city_name']} ({r['province_name']}): {r['price_per_sqm']:,.0f}  (listings: {r['listing_count']})")

    path = data_dir / "city_price.json"
    path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved to {path}")


if __name__ == "__main__":
    main()
