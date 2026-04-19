# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python project for collecting, analyzing, and visualizing real estate data (housing prices, rental prices, etc.). The working name is "房价地图" (housing price map). It currently compares housing strategies: renting, buying with a loan, and buying outright.

## Tech Stack

- **Language**: Python 3.12+
- **Package Manager**: [uv](https://docs.astral.sh/uv/)
- **Dependencies**: None yet (defined in `pyproject.toml`)

## Common Commands

```bash
# Run the main script
uv run main.py

# Add a dependency
uv add <package>

# Add a dev dependency
uv add --dev <package>

# Update lockfile
uv lock
```

## Project Structure

- `main.py` — Entry point (currently a placeholder).
- `pyproject.toml` — Project metadata and dependencies.
- `uv.lock` — Lockfile for reproducible installs.
- `scripts/` — Empty directory intended for utility scripts.

## Notes

- The project is in early stages. There is no test suite, no CI, and no build step yet.
- The README (`README.md`) is written in Chinese.
