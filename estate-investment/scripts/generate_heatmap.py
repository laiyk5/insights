from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path so 'insights' and 'scripts' packages are importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from insights.estate.mock_data import generate_hongkong_mock_data, generate_shenzhen_mock_data
from scripts.visualization import draw_price_heatmap


def main():
    shenzhen = generate_shenzhen_mock_data(estates_per_district=30)
    hongkong = generate_hongkong_mock_data(estates_per_district=30)
    all_prices = shenzhen + hongkong
    output_dir = Path(__file__).resolve().parent.parent / "outputs"
    output_dir.mkdir(exist_ok=True)
    draw_price_heatmap(all_prices, output_path=str(output_dir / "estate_price_heatmap.html"))


if __name__ == "__main__":
    main()
