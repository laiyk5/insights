"""Calculate buy-vs-rent net profit for 322 cities and visualize."""
from __future__ import annotations

import json
import math
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


def calculate_net_profit(
    price_per_sqm: float,
    rent_per_sqm_monthly: float,
    years: int = 30,
    opportunity_rate: float = 0.04,
    appreciation_rate: float = 0.02,
) -> dict:
    """Calculate net profit of buying vs renting over a holding period.

    Model (aligned with README):
    - Renting: pay rent every month, no asset at the end
    - Buying (cash): pay full price now, own the house at the end
      - Cost = price * (1 + opportunity_rate)^years  (compounded opportunity cost)
      - Benefit = price * (1 + appreciation_rate)^years  (residual value)

    Net profit of buying vs renting =
        (benefit_buy - cost_buy) - (-total_rent)
        = residual_value - price*(1+r)^years + total_rent
    """
    total_rent = rent_per_sqm_monthly * 12 * years
    buy_cost = price_per_sqm * ((1 + opportunity_rate) ** years)
    residual_value = price_per_sqm * ((1 + appreciation_rate) ** years)

    net_profit = residual_value - buy_cost + total_rent

    # Also compute price-to-rent ratio for reference
    annual_rent = rent_per_sqm_monthly * 12
    price_to_rent = price_per_sqm / annual_rent if annual_rent > 0 else float("inf")

    # Break-even appreciation rate (where net_profit = 0)
    # residual_value = buy_cost - total_rent
    # price * (1 + breakeven)^years = buy_cost - total_rent
    breakeven_numerator = buy_cost - total_rent
    if breakeven_numerator > 0 and price_per_sqm > 0:
        breakeven_rate = (breakeven_numerator / price_per_sqm) ** (1 / years) - 1
    else:
        breakeven_rate = float("inf")

    return {
        "total_rent_30yr": round(total_rent, 2),
        "buy_cost_30yr": round(buy_cost, 2),
        "residual_value": round(residual_value, 2),
        "net_profit": round(net_profit, 2),
        "price_to_rent_ratio": round(price_to_rent, 1),
        "breakeven_appreciation_rate": round(breakeven_rate * 100, 2),
    }


def merge_city_data() -> list[dict]:
    """Merge price and rent data by city name."""
    prices = {p["city_name"]: p for p in load_json("city_price.json")}
    rents = {r["city_name"]: r for r in load_json("city_rent.json")}
    coords = load_coord_cache()

    results = []
    for city in sorted(set(prices.keys()) & set(rents.keys())):
        p = prices[city]
        r = rents[city]

        # Calculate for different appreciation scenarios
        scenario_0 = calculate_net_profit(p["price_per_sqm"], r["rent_per_sqm_monthly"], appreciation_rate=0.00)
        scenario_2 = calculate_net_profit(p["price_per_sqm"], r["rent_per_sqm_monthly"], appreciation_rate=0.02)
        scenario_4 = calculate_net_profit(p["price_per_sqm"], r["rent_per_sqm_monthly"], appreciation_rate=0.04)

        results.append({
            "city_name": city,
            "province_name": p["province_name"],
            "price_per_sqm": p["price_per_sqm"],
            "rent_per_sqm_monthly": r["rent_per_sqm_monthly"],
            "listing_count": p["listing_count"],
            "lat": coords.get(city, [None, None])[0],
            "lon": coords.get(city, [None, None])[1],
            "scenario_0pct": scenario_0,
            "scenario_2pct": scenario_2,
            "scenario_4pct": scenario_4,
        })

    return results


def profit_color(profit: float) -> str:
    if profit >= 50000:
        return "#15803d"  # dark green - buying much better
    if profit >= 0:
        return "#16a34a"  # green - buying slightly better
    if profit >= -50000:
        return "#ca8a04"  # yellow - renting slightly better
    if profit >= -150000:
        return "#ea580c"  # orange - renting better
    return "#dc2626"  # red - renting much better


def build_map(cities: list[dict], scenario_key: str = "scenario_2pct") -> folium.Map:
    """Build an interactive map colored by buy-vs-rent net profit."""
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
        profit = c[scenario_key]["net_profit"]
        ptr = c[scenario_key]["price_to_rent_ratio"]
        listings = c["listing_count"]
        radius = max(4, min(28, (listings ** 0.5) / 18))
        color = profit_color(profit)

        popup_html = (
            f"<b>{c['city_name']}</b> ({c['province_name']})<br>"
            f"房价: {c['price_per_sqm']:,.0f} ¥/m²<br>"
            f"租金: {c['rent_per_sqm_monthly']:.0f} ¥/m²/月<br>"
            f"租售比: {ptr:.1f}<br>"
            f"<b>30年净收益(买房-租房): {profit:,.0f} ¥/m²</b><br>"
            f"<small>假设: 房价年增值{c['scenario_2pct']['breakeven_appreciation_rate']:.1f}%可盈亏平衡</small>"
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
        <b>30年买房 vs 租房 净收益 (¥/m²)</b><br>
        <small>假设房价年增值2%，机会成本4%</small><br>
        <span style="color:#15803d">&#9679;</span> ≥ +5万 (买房明显划算)<br>
        <span style="color:#16a34a">&#9679;</span> 0 ~ +5万 (买房略划算)<br>
        <span style="color:#ca8a04">&#9679;</span> -5万 ~ 0 (租房略划算)<br>
        <span style="color:#ea580c">&#9679;</span> -15万 ~ -5万 (租房划算)<br>
        <span style="color:#dc2626">&#9679;</span> &lt; -15万 (租房明显划算)
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    return m


def main():
    print("Calculating buy-vs-rent net profit for all cities...")
    cities = merge_city_data()
    print(f"Merged {len(cities)} cities with both price and rent data")

    # Save results
    path = _data_dir() / "buy_vs_rent.json"
    path.write_text(json.dumps(cities, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved calculations to {path}")

    # Print summary
    profits_2pct = [c["scenario_2pct"]["net_profit"] for c in cities]
    buy_better = sum(1 for p in profits_2pct if p > 0)
    rent_better = sum(1 for p in profits_2pct if p < 0)

    print(f"\n=== 假设房价年增值2%，机会成本4%，持有30年 ===")
    print(f"买房更划算的城市: {buy_better} 个")
    print(f"租房更划算的城市: {rent_better} 个")

    top_buy = sorted(cities, key=lambda c: c["scenario_2pct"]["net_profit"], reverse=True)[:5]
    print(f"\n买房最划算的5个城市:")
    for c in top_buy:
        p = c["scenario_2pct"]["net_profit"]
        print(f"  {c['city_name']}: +{p:,.0f} ¥/m²")

    top_rent = sorted(cities, key=lambda c: c["scenario_2pct"]["net_profit"])[:5]
    print(f"\n租房最划算的5个城市:")
    for c in top_rent:
        p = c["scenario_2pct"]["net_profit"]
        print(f"  {c['city_name']}: {p:,.0f} ¥/m²")

    # Build map
    print("\nGenerating map...")
    m = build_map(cities, scenario_key="scenario_2pct")
    output_dir = Path(__file__).resolve().parent.parent / "outputs"
    output_dir.mkdir(exist_ok=True)
    map_path = output_dir / "buy_vs_rent_map.html"
    m.save(str(map_path))
    print(f"Map saved to {map_path}")


if __name__ == "__main__":
    main()
