"""Geocode cities and visualize rental data on an interactive map."""
from __future__ import annotations

import json
import sys
import time
from datetime import date
from pathlib import Path

import folium
from geopy.geocoders import Nominatim

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _data_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data"


def load_rent_data() -> list[dict]:
    path = _data_dir() / "city_rent.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_coord_cache() -> dict[str, tuple[float, float]]:
    path = _data_dir() / "city_coords_cache.json"
    if path.exists():
        raw = json.loads(path.read_text(encoding="utf-8"))
        return {k: tuple(v) for k, v in raw.items()}
    return {}


def save_coord_cache(cache: dict[str, tuple[float, float]]) -> None:
    path = _data_dir() / "city_coords_cache.json"
    serializable = {k: list(v) for k, v in cache.items()}
    path.write_text(json.dumps(serializable, indent=2, ensure_ascii=False), encoding="utf-8")


def geocode_cities(rent_data: list[dict], cache: dict[str, tuple[float, float]]) -> dict[str, tuple[float, float]]:
    """Geocode missing cities using Nominatim (1 req/sec)."""
    geolocator = Nominatim(user_agent="estate-investment-visualizer/1.0")
    updated = dict(cache)
    missing = [r for r in rent_data if r["city_name"] not in updated]

    if not missing:
        print("All cities already geocoded (cache hit).")
        return updated

    print(f"Geocoding {len(missing)} cities with Nominatim (1 req/sec)...")
    for i, rec in enumerate(missing, 1):
        city = rec["city_name"]
        province = rec["province_name"]
        query = f"{city}, {province}, China"
        try:
            location = geolocator.geocode(query, timeout=10)
            if location:
                updated[city] = (location.latitude, location.longitude)
                print(f"  [{i}/{len(missing)}] {city} -> {location.latitude:.4f}, {location.longitude:.4f}")
            else:
                print(f"  [{i}/{len(missing)}] {city} -> NOT FOUND")
        except Exception as e:
            print(f"  [{i}/{len(missing)}] {city} -> ERROR: {e}")
        time.sleep(1.1)

    save_coord_cache(updated)
    print(f"Cached {len(updated)} coordinates.")
    return updated


def rent_color(rent: float) -> str:
    if rent >= 70:
        return "#7c3aed"  # purple
    if rent >= 50:
        return "#dc2626"  # red
    if rent >= 35:
        return "#ea580c"  # orange
    if rent >= 25:
        return "#ca8a04"  # yellow/amber
    if rent >= 15:
        return "#16a34a"  # green
    return "#15803d"  # dark green


def build_map(rent_data: list[dict], coords: dict[str, tuple[float, float]]) -> folium.Map:
    """Build a folium map with circle markers for each city."""
    matched = [(r, coords[r["city_name"]]) for r in rent_data if r["city_name"] in coords]
    if not matched:
        raise ValueError("No cities with coordinates to display")

    avg_lat = sum(c[0] for _, c in matched) / len(matched)
    avg_lon = sum(c[1] for _, c in matched) / len(matched)

    m = folium.Map(
        location=[avg_lat, avg_lon],
        zoom_start=5,
        tiles="CartoDB positron",
    )

    for rec, (lat, lon) in matched:
        rent = rec["rent_per_sqm_monthly"]
        listings = rec["listing_count"]
        radius = max(4, min(28, (listings ** 0.5) / 18))
        color = rent_color(rent)

        popup_html = (
            f"<b>{rec['city_name']}</b> ({rec['province_name']})<br>"
            f"Rent: <b>{rent:.0f}</b> ¥/m²/month<br>"
            f"Listings: {listings:,}<br>"
            f"Recorded: {rec.get('recorded_at', date.today().isoformat())}"
        )

        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            popup=folium.Popup(popup_html, max_width=220),
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            color="#333333",
            weight=1,
        ).add_to(m)

    # Legend
    legend_html = """
    <div style="position: fixed; bottom: 20px; right: 20px;
                background: rgba(255,255,255,0.95); padding: 12px 16px;
                border-radius: 6px; font-size: 13px; line-height: 1.6;
                box-shadow: 0 1px 5px rgba(0,0,0,0.2); z-index: 9999;">
        <b>Rent (¥/m²/month)</b><br>
        <span style="color:#7c3aed">&#9679;</span> ≥ 70<br>
        <span style="color:#dc2626">&#9679;</span> 50 – 70<br>
        <span style="color:#ea580c">&#9679;</span> 35 – 50<br>
        <span style="color:#ca8a04">&#9679;</span> 25 – 35<br>
        <span style="color:#16a34a">&#9679;</span> 15 – 25<br>
        <span style="color:#15803d">&#9679;</span> &lt; 15
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    return m


def main():
    rent_data = load_rent_data()
    print(f"Loaded {len(rent_data)} cities from city_rent.json")

    cache = load_coord_cache()
    coords = geocode_cities(rent_data, cache)

    matched_count = sum(1 for r in rent_data if r["city_name"] in coords)
    print(f"\nMapping {matched_count}/{len(rent_data)} cities")

    m = build_map(rent_data, coords)
    output_dir = _data_dir().parent / "outputs"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "city_rent_map.html"
    m.save(str(output_path))
    print(f"Map saved to {output_path}")


if __name__ == "__main__":
    main()
