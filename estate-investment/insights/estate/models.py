from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class GeoLocation:
    latitude: float
    longitude: float


@dataclass(frozen=True)
class Address:
    city: str
    province: str
    country: str
    district: str | None = None
    subdistrict: str | None = None


@dataclass
class Country:
    name: str
    provinces: list[Province] = field(default_factory=list)


@dataclass
class Province:
    name: str
    country: Country
    cities: list[City] = field(default_factory=list)


@dataclass
class City:
    name: str
    province: Province
    districts: list[District] = field(default_factory=list)


@dataclass
class District:
    name: str
    city: City
    subdistricts: list[SubDistrict] = field(default_factory=list)


@dataclass
class SubDistrict:
    name: str
    district: District


@dataclass(frozen=True)
class Estate:
    name: str
    age: int
    geo_location: GeoLocation
    address: Address
    district: District


@dataclass(frozen=True)
class EstatePrice:
    estate: Estate
    price_per_sqm: float
    total_price: float
    recorded_at: date = field(default_factory=date.today)


@dataclass(frozen=True)
class AveragePrice:
    area: District | City | Province | Country
    avg_price_per_sqm: float
    sample_count: int
    recorded_at: date = field(default_factory=date.today)


@dataclass(frozen=True)
class CityRent:
    """Rental market data for a city from cityre.cn."""
    city_name: str
    province_name: str
    listing_count: int
    rent_per_sqm_monthly: float
    recorded_at: date = field(default_factory=date.today)
