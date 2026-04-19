from __future__ import annotations

import json
from pathlib import Path

from .models import (
    Address,
    City,
    Country,
    District,
    Estate,
    EstatePrice,
    GeoLocation,
    Province,
    SubDistrict,
)


def _data_dir() -> Path:
    """Return the project's data/ directory."""
    # This file is at insights/estate/mock_data.py; project root is 3 levels up.
    return Path(__file__).resolve().parent.parent.parent / "data"


def _load_estate_prices(json_path: Path) -> list[EstatePrice]:
    """Load a list of EstatePrice objects from a flat JSON file."""
    records = json.loads(json_path.read_text(encoding="utf-8"))

    china = Country(name="China")
    provinces: dict[str, Province] = {}
    cities: dict[str, City] = {}
    districts: dict[str, District] = {}
    subdistricts: dict[str, SubDistrict] = {}
    estate_prices: list[EstatePrice] = []

    for rec in records:
        # Build or reuse province
        province_name = rec["province"]
        if province_name not in provinces:
            province = Province(name=province_name, country=china)
            china.provinces.append(province)
            provinces[province_name] = province
        else:
            province = provinces[province_name]

        # Build or reuse city
        city_name = rec["city"]
        city_key = f"{province_name}:{city_name}"
        if city_key not in cities:
            city = City(name=city_name, province=province)
            province.cities.append(city)
            cities[city_key] = city
        else:
            city = cities[city_key]

        # Build or reuse district
        district_name = rec["district"]
        district_key = f"{city_key}:{district_name}"
        if district_key not in districts:
            district = District(name=district_name, city=city)
            city.districts.append(district)
            districts[district_key] = district
        else:
            district = districts[district_key]

        # Build or reuse subdistrict
        subdistrict_name = rec["subdistrict"]
        sub_key = f"{district_key}:{subdistrict_name}"
        if sub_key not in subdistricts:
            sub = SubDistrict(name=subdistrict_name, district=district)
            district.subdistricts.append(sub)
            subdistricts[sub_key] = sub
        else:
            sub = subdistricts[sub_key]

        estate = Estate(
            name=rec["name"],
            age=rec["age"],
            geo_location=GeoLocation(
                latitude=rec["latitude"],
                longitude=rec["longitude"],
            ),
            address=Address(
                city=rec["city"],
                province=rec["province"],
                country=rec["country"],
                district=rec["district"],
                subdistrict=rec["subdistrict"],
            ),
            district=district,
        )

        estate_prices.append(
            EstatePrice(
                estate=estate,
                price_per_sqm=rec["price_per_sqm"],
                total_price=rec["total_price"],
            )
        )

    return estate_prices


def generate_shenzhen_mock_data(estates_per_district: int = 30) -> list[EstatePrice]:
    """Load pre-defined Shenzhen estate data from data/shenzhen.json."""
    return _load_estate_prices(_data_dir() / "shenzhen.json")


def generate_hongkong_mock_data(estates_per_district: int = 30) -> list[EstatePrice]:
    """Load pre-defined Hong Kong estate data from data/hongkong.json."""
    return _load_estate_prices(_data_dir() / "hongkong.json")
