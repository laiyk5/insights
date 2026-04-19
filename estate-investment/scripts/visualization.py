from __future__ import annotations

import folium
from folium.plugins import HeatMap

from insights.estate.models import EstatePrice


def draw_price_heatmap(
    estate_prices: list[EstatePrice],
    output_path: str = "outputs/estate_price_heatmap.html",
) -> None:
    """Draw an estate price heatmap and save it to an HTML file."""
    if not estate_prices:
        raise ValueError("No estate prices provided")

    # Compute map center from data
    avg_lat = sum(ep.estate.geo_location.latitude for ep in estate_prices) / len(estate_prices)
    avg_lon = sum(ep.estate.geo_location.longitude for ep in estate_prices) / len(estate_prices)

    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=11, tiles="CartoDB positron")

    # Prepare heat data: [lat, lon, intensity]
    # Normalize price for intensity (0-1 range)
    prices = [ep.price_per_sqm for ep in estate_prices]
    min_p, max_p = min(prices), max(prices)
    price_range = max_p - min_p if max_p != min_p else 1

    heat_data = [
        [
            ep.estate.geo_location.latitude,
            ep.estate.geo_location.longitude,
            (ep.price_per_sqm - min_p) / price_range,
        ]
        for ep in estate_prices
    ]

    HeatMap(heat_data, radius=15, blur=25, max_zoom=13).add_to(m)

    # Add markers for top 5 most expensive estates
    top5 = sorted(estate_prices, key=lambda ep: ep.price_per_sqm, reverse=True)[:5]
    for ep in top5:
        folium.Marker(
            location=[ep.estate.geo_location.latitude, ep.estate.geo_location.longitude],
            popup=folium.Popup(
                f"<b>{ep.estate.name}</b><br>"
                f"Price: ¥{ep.price_per_sqm:,.0f}/m²<br>"
                f"Total: ¥{ep.total_price:,.0f}",
                max_width=200,
            ),
            icon=folium.Icon(color="red", icon="home"),
        ).add_to(m)

    m.save(output_path)
    print(f"Heatmap saved to {output_path}")
