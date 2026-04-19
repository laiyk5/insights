"""Download city rental market data from cityre.cn API."""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from insights.estate.models import CityRent


def fetch_city_rent_data() -> list[CityRent]:
    """Fetch rental data for all cities from cityre.cn."""
    url = "https://www.cityre.cn/target/gethousingPriceList"
    params = {"queryType": "houseRent"}
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    raw_data = resp.json()

    records: list[CityRent] = []
    for item in raw_data:
        records.append(
            CityRent(
                city_name=item["cityName"],
                province_name=item["provinceName"],
                listing_count=int(item["priceCount"]),
                rent_per_sqm_monthly=float(item["unitPrice"]),
            )
        )
    return records


def save_to_json(records: list[CityRent], path: Path) -> None:
    """Serialize CityRent records to JSON."""
    data = [
        {
            "city_name": r.city_name,
            "province_name": r.province_name,
            "listing_count": r.listing_count,
            "rent_per_sqm_monthly": r.rent_per_sqm_monthly,
            "recorded_at": r.recorded_at.isoformat(),
        }
        for r in records
    ]
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {len(records)} records to {path}")


def main():
    data_dir = Path(__file__).resolve().parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    print("Fetching city rental data from cityre.cn...")
    records = fetch_city_rent_data()
    print(f"Fetched {len(records)} cities")

    # Sort by rent descending for a quick preview
    top10 = sorted(records, key=lambda r: r.rent_per_sqm_monthly, reverse=True)[:10]
    print("\nTop 10 most expensive cities (元/月/平米):")
    for r in top10:
        print(f"  {r.city_name} ({r.province_name}): {r.rent_per_sqm_monthly}  (listings: {r.listing_count})")

    save_to_json(records, data_dir / "city_rent.json")


if __name__ == "__main__":
    main()
