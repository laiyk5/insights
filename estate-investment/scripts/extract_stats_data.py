"""Extract table data from stats.gov.cn yearbook images using OCR."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytesseract
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def extract_text_from_image(image_path: str) -> str:
    """Use OCR to extract text from an image."""
    img = Image.open(image_path)
    # Use Chinese + English language support
    text = pytesseract.image_to_string(img, lang="chi_sim+eng")
    return text


def parse_price_table(text: str) -> list[dict]:
    """Parse OCR text from table 19-11 (average sales prices)."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    records = []

    # The table has years as columns and housing types as rows
    # Expected format: headers with years, then rows with data
    # Let's try to find year headers and numeric data

    year_pattern = re.compile(r"20\d{2}")
    number_pattern = re.compile(r"(\d{3,5})\.(\d{2})")

    years = []
    current_category = None

    for line in lines:
        # Detect year headers
        year_matches = year_pattern.findall(line)
        if year_matches and not years:
            years = [int(y) for y in year_matches]
            continue

        # Detect category rows
        if "住宅" in line or "商品房" in line or "办公楼" in line or "商业营业用房" in line:
            current_category = line.split()[0] if line.split() else line
            continue

        # Extract numbers
        numbers = number_pattern.findall(line)
        if numbers and current_category and years:
            # Map numbers to years
            for i, (whole, frac) in enumerate(numbers):
                if i < len(years):
                    value = float(f"{whole}.{frac}")
                    records.append({
                        "year": years[i],
                        "category": current_category,
                        "price_per_sqm": value,
                    })

    return records


def save_extracted_data(records: list[dict], output_path: Path) -> None:
    """Save extracted records to JSON."""
    output_path.write_text(
        json.dumps(records, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Saved {len(records)} records to {output_path}")


def main():
    data_dir = Path(__file__).resolve().parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    # Extract from C19-11 (average sales price)
    print("Extracting C19-11 (average sales price)...")
    text_19_11 = extract_text_from_image("/tmp/C19-11.jpg")
    print("--- Raw OCR output (first 500 chars) ---")
    print(text_19_11[:500])
    print("--- End preview ---")

    records_19_11 = parse_price_table(text_19_11)
    if records_19_11:
        save_extracted_data(records_19_11, data_dir / "C19-11_prices.json")
    else:
        print("No records extracted from C19-11")
        # Save raw text for manual inspection
        (data_dir / "C19-11_raw.txt").write_text(text_19_11, encoding="utf-8")
        print(f"Saved raw OCR text to {data_dir / 'C19-11_raw.txt'}")

    # Extract from C19-14 (regional investment)
    print("\nExtracting C19-14 (regional investment)...")
    text_19_14 = extract_text_from_image("/tmp/C19-14.jpg")
    print("--- Raw OCR output (first 500 chars) ---")
    print(text_19_14[:500])
    print("--- End preview ---")

    (data_dir / "C19-14_raw.txt").write_text(text_19_14, encoding="utf-8")
    print(f"Saved raw OCR text to {data_dir / 'C19-14_raw.txt'}")


if __name__ == "__main__":
    main()
