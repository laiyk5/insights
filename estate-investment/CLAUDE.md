# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tech Stack

- **Language**: Python 3.13+
- **Package Manager**: [uv](https://docs.astral.sh/uv/)
- **Key Dependencies**: `folium` (interactive maps), `geopy` (Nominatim geocoding), `requests` (data fetching), `pillow` + `pytesseract` (OCR for stats.gov.cn yearbook images)

## Common Commands

All scripts are standalone and run directly with `uv run`:

```bash
# Install dependencies
uv sync

# Fetch data from cityre.cn
uv run scripts/fetch_city_rent.py
uv run scripts/fetch_city_price.py

# Run analyses and generate maps
uv run scripts/calculate_buy_vs_rent.py      #买房 vs 租房净收益
uv run scripts/calculate_rental_yield.py     # 租金回报率
uv run scripts/visualize_city_rent.py        # 城市租金水平（also geocodes cities）
uv run scripts/generate_heatmap.py           # 深圳/香港房价热力图

# View results
open outputs/*.html
```

There is no test suite, build step, or CI yet.

## Architecture

### Data Flow

The pipeline is file-based and sequential:

1. **Fetch** (`fetch_city_rent.py`, `fetch_city_price.py`) → downloads from cityre.cn API → `data/city_rent.json`, `data/city_price.json`
2. **Geocode** (`visualize_city_rent.py`) → queries Nominatim (1 req/sec, cached) → `data/city_coords_cache.json`
3. **Analyze** (`calculate_buy_vs_rent.py`, `calculate_rental_yield.py`) → reads JSON, computes metrics → `data/buy_vs_rent.json`, `data/rental_yield.json`
4. **Visualize** → generates interactive folium maps → `outputs/*.html`

### Script Conventions

- Every script in `scripts/` is self-contained and executable directly. There is no `main.py` entry point.
- Scripts use `sys.path.insert(0, str(Path(__file__).resolve().parent.parent))` to make the `insights` package importable, since it is not installed as a package.
- A `_data_dir()` helper is duplicated across scripts; it resolves to `<project_root>/data`.

### Visualization Pattern

All folium maps follow the same pattern:
- **Tile layer**: `CartoDB positron`
- **Markers**: `folium.CircleMarker` with `fill_opacity=0.75`
- **Radius**: scaled by `max(4, min(28, (listings ** 0.5) / 18))` — larger markets get bigger circles
- **Color**: metric-dependent (green/yellow/orange/red tiers defined per script)
- **Legend**: HTML element injected via `folium.Element` at fixed bottom-right position
- **Popup**: HTML string with city name, province, key metrics

### Core Models

`insights/estate/` contains the domain models (`GeoLocation`, `Address`, `City`, `District`, `Estate`, `EstatePrice`, `CityRent`, etc.) and `mock_data.py` which loads static JSON files (`data/shenzhen.json`, `data/hongkong.json`) into typed objects. The package is imported by `generate_heatmap.py` and `visualization.py` but most analysis scripts bypass the models and work with raw `dict`s loaded from JSON.

### Data Sources

- **City rent/price**: [cityre.cn](https://www.cityre.cn) API (`gethousingPriceList?queryType=houseRent` / `housingPrice`), covering ~322 Chinese cities.
- **Shenzhen/Hong Kong**: Mock data in `data/shenzhen.json` and `data/hongkong.json` (static, district-level).
- **stats.gov.cn**: OCR extraction script (`extract_stats_data.py`) for yearbook table images; currently saves raw OCR text to `data/C19-11_raw.txt` and `data/C19-14_raw.txt`.

### Geocoding Cache

`visualize_city_rent.py` is the only script that geocodes. It uses `geopy.Nominatim` with a 1.1s sleep between requests and persists results to `data/city_coords_cache.json`. All other visualization scripts read this cache via `load_coord_cache()`. If a city is missing coordinates, its marker is silently skipped.

## Publishing Protocol

This subproject participates in the umbrella `insights` GitHub Pages site. To be included, it provides `site-manifest.json` at its root, which declares the HTML visualizations in `outputs/` that should be published. The site builder at `site-builder/` auto-discovers this manifest and generates the subproject's page. See the root `README.md` for the full protocol specification.

## Notes

- The buy-vs-rent model (`calculate_buy_vs_rent.py`) uses a simplified cash-buy scenario: net profit = residual_value - opportunity_cost + total_rent. It does not model mortgages, leverage, or cash flow.
- The README (`README.md`) is in Chinese and contains detailed calculation assumptions and sample results.
