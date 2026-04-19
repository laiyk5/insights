"""Calculate and visualize rental yield (annual rent / price) for 322 cities."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import folium

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _data_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data"


def load_json(filename: str) -> list[dict]:
    path = _data_dir() / filename
    return json.loads(path.read_text(encoding="utf-8"))


def load_coord_cache() -> dict[str, tuple[float, float]]:
    path = _data_dir() / "city_coords_cache.json"
    if path.exists():
        raw = json.loads(path.read_text(encoding="utf-8"))
        return {k: tuple(v) for k, v in raw.items()}
    return {}


def calculate_rental_yield(price_per_sqm: float, rent_per_sqm_monthly: float) -> float:
    """Annual rental yield = annual rent / price."""
    annual_rent = rent_per_sqm_monthly * 12
    return (annual_rent / price_per_sqm) * 100 if price_per_sqm > 0 else 0


def merge_and_calculate() -> list[dict]:
    prices = {p["city_name"]: p for p in load_json("city_price.json")}
    rents = {r["city_name"]: r for r in load_json("city_rent.json")}
    coords = load_coord_cache()

    results = []
    for city in sorted(set(prices.keys()) & set(rents.keys())):
        p = prices[city]
        r = rents[city]
        yield_pct = calculate_rental_yield(p["price_per_sqm"], r["rent_per_sqm_monthly"])

        results.append({
            "city_name": city,
            "province_name": p["province_name"],
            "price_per_sqm": p["price_per_sqm"],
            "rent_per_sqm_monthly": r["rent_per_sqm_monthly"],
            "annual_rent_per_sqm": r["rent_per_sqm_monthly"] * 12,
            "rental_yield_pct": round(yield_pct, 2),
            "listing_count": p["listing_count"],
            "lat": coords.get(city, [None, None])[0],
            "lon": coords.get(city, [None, None])[1],
        })

    return results


def yield_color(yield_pct: float) -> str:
    if yield_pct >= 4.0:
        return "#15803d"  # dark green - excellent yield
    if yield_pct >= 3.0:
        return "#16a34a"  # green - good yield
    if yield_pct >= 2.0:
        return "#ca8a04"  # yellow - moderate
    if yield_pct >= 1.5:
        return "#ea580c"  # orange - low
    return "#dc2626"  # red - very low


def build_map(cities: list[dict]) -> folium.Map:
    matched = [c for c in cities if c["lat"] is not None]
    if not matched:
        raise ValueError("No cities with coordinates")

    avg_lat = sum(c["lat"] for c in matched) / len(matched)
    avg_lon = sum(c["lon"] for c in matched) / len(matched)

    m = folium.Map(
        location=[avg_lat, avg_lon],
        zoom_start=5,
        tiles="CartoDB positron",
    )

    for c in matched:
        y = c["rental_yield_pct"]
        listings = c["listing_count"]
        radius = max(4, min(28, (listings ** 0.5) / 18))
        color = yield_color(y)

        popup_html = (
            f"<b>{c['city_name']}</b> ({c['province_name']})<br>"
            f"房价: {c['price_per_sqm']:,.0f} ¥/m²<br>"
            f"月租: {c['rent_per_sqm_monthly']:.0f} ¥/m²/月<br>"
            f"年租: {c['annual_rent_per_sqm']:,.0f} ¥/m²/年<br>"
            f"<b>租金回报率: {y:.2f}%</b><br>"
            f"挂牌量: {listings:,}"
        )

        folium.CircleMarker(
            location=[c["lat"], c["lon"]],
            radius=radius,
            popup=folium.Popup(popup_html, max_width=260),
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            color="#333333",
            weight=1,
        ).add_to(m)

    legend_html = """
    <div style="position: fixed; bottom: 20px; right: 20px;
                background: rgba(255,255,255,0.95); padding: 12px 16px;
                border-radius: 6px; font-size: 13px; line-height: 1.6;
                box-shadow: 0 1px 5px rgba(0,0,0,0.2); z-index: 9999;">
        <b>租金回报率 (年租金 / 房价)</b><br>
        <span style="color:#15803d">&#9679;</span> ≥ 4.0% (优秀)<br>
        <span style="color:#16a34a">&#9679;</span> 3.0% ~ 4.0% (良好)<br>
        <span style="color:#ca8a04">&#9679;</span> 2.0% ~ 3.0% (一般)<br>
        <span style="color:#ea580c">&#9679;</span> 1.5% ~ 2.0% (偏低)<br>
        <span style="color:#dc2626">&#9679;</span> &lt; 1.5% (极低)
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    return m


def main():
    print("Calculating rental yield for all cities...")
    cities = merge_and_calculate()
    print(f"Calculated {len(cities)} cities")

    # Save results
    path = _data_dir() / "rental_yield.json"
    path.write_text(json.dumps(cities, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved to {path}")

    # Summary
    avg_yield = sum(c["rental_yield_pct"] for c in cities) / len(cities)
    print(f"\n平均租金回报率: {avg_yield:.2f}%")

    top = sorted(cities, key=lambda c: c["rental_yield_pct"], reverse=True)[:10]
    print("\n租金回报率最高的10个城市:")
    for c in top:
        print(f"  {c['city_name']}: {c['rental_yield_pct']:.2f}%  "
              f"(房价{c['price_per_sqm']:,.0f}, 月租{c['rent_per_sqm_monthly']:.0f})")

    bottom = sorted(cities, key=lambda c: c["rental_yield_pct"])[:10]
    print("\n租金回报率最低的10个城市:")
    for c in bottom:
        print(f"  {c['city_name']}: {c['rental_yield_pct']:.2f}%  "
              f"(房价{c['price_per_sqm']:,.0f}, 月租{c['rent_per_sqm_monthly']:.0f})")

    # Build map
    print("\nGenerating map...")
    m = build_map(cities)
    output_dir = Path(__file__).resolve().parent.parent / "outputs"
    output_dir.mkdir(exist_ok=True)
    map_path = output_dir / "rental_yield_map.html"
    m.save(str(map_path))
    print(f"Map saved to {map_path}")


if __name__ == "__main__":
    main()
