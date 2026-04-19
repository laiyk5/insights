"""Build a static site by auto-discovering subproject manifests."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape


def _repo_root() -> Path:
    # site_builder is at site-builder/site_builder/builder.py
    return Path(__file__).resolve().parent.parent.parent


def _template_dir() -> Path:
    return Path(__file__).resolve().parent / "templates"


def load_site_config() -> dict:
    path = _repo_root() / "site-config.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"title": "Insights", "description": "Data mining & visualizations"}


def discover_manifests() -> list[tuple[Path, dict]]:
    """Scan top-level directories for site-manifest.json files."""
    root = _repo_root()
    results: list[tuple[Path, dict]] = []
    for subdir in root.iterdir():
        if not subdir.is_dir():
            continue
        if subdir.name.startswith(".") or subdir.name in {"docs", "site-builder"}:
            continue
        manifest_path = subdir / "site-manifest.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            results.append((subdir, manifest))
    # Sort by route for deterministic order
    results.sort(key=lambda x: x[1].get("route", x[0].name))
    return results


def copy_outputs(subproject_dir: Path, manifest: dict, docs_dir: Path) -> None:
    """Copy output HTML files and optional site-assets into docs/."""
    route = manifest.get("route", subproject_dir.name)
    target = docs_dir / route
    target.mkdir(parents=True, exist_ok=True)

    outputs_dir = subproject_dir / "outputs"
    if outputs_dir.exists():
        for html_file in outputs_dir.glob("*.html"):
            shutil.copy2(html_file, target / html_file.name)

    assets_dir = subproject_dir / "site-assets"
    if assets_dir.exists():
        target_assets = target / "assets"
        if target_assets.exists():
            shutil.rmtree(target_assets)
        shutil.copytree(assets_dir, target_assets)


def build() -> None:
    """Generate the static site into docs/."""
    root = _repo_root()
    docs_dir = root / "docs"
    if docs_dir.exists():
        shutil.rmtree(docs_dir)
    docs_dir.mkdir(exist_ok=True)

    config = load_site_config()
    manifests = discover_manifests()

    if not manifests:
        print("No site-manifest.json files found.")
        sys.exit(1)

    env = Environment(
        loader=FileSystemLoader(str(_template_dir())),
        autoescape=select_autoescape(["html", "xml"]),
    )

    # Shared static assets
    static_dir = docs_dir / "static"
    static_dir.mkdir(exist_ok=True)
    (static_dir / "style.css").write_text(_static_css(), encoding="utf-8")

    # Tell GitHub Pages to skip Jekyll (serve static files as-is)
    (docs_dir / ".nojekyll").touch()

    # Build subproject detail pages
    for subproject_dir, manifest in manifests:
        route = manifest.get("route", subproject_dir.name)
        copy_outputs(subproject_dir, manifest, docs_dir)

        template = env.get_template("subproject.html")
        html = template.render(
            site=config,
            subproject=manifest,
            route=route,
            base_path="../",
        )
        (docs_dir / route / "index.html").write_text(html, encoding="utf-8")
        print(f"  Built /{route}/ ({manifest.get('name', route)})")

    # Build landing page
    template = env.get_template("index.html")
    html = template.render(
        site=config,
        subprojects=[m for _, m in manifests],
        base_path="",
    )
    (docs_dir / "index.html").write_text(html, encoding="utf-8")
    print(f"Built {docs_dir}/index.html")


def _static_css() -> str:
    return """\
:root {
  --bg: #f8f9fa;
  --fg: #212529;
  --muted: #6c757d;
  --card-bg: #ffffff;
  --accent: #0d6efd;
  --border: #dee2e6;
  --radius: 8px;
}

* { box-sizing: border-box; }

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
               "Helvetica Neue", Arial, sans-serif;
  background: var(--bg);
  color: var(--fg);
  line-height: 1.6;
  margin: 0;
  padding: 0;
}

.container {
  max-width: 960px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

header {
  text-align: center;
  margin-bottom: 2.5rem;
}

header h1 {
  font-size: 2rem;
  margin: 0 0 0.25rem;
}

header p {
  color: var(--muted);
  margin: 0;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.25rem;
  transition: box-shadow 0.15s ease;
  text-decoration: none;
  color: inherit;
  display: block;
}

.card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

.card h2 {
  font-size: 1.15rem;
  margin: 0 0 0.5rem;
  color: var(--accent);
}

.card p {
  margin: 0;
  color: var(--muted);
  font-size: 0.95rem;
}

.viz-list {
  list-style: none;
  padding: 0;
  margin: 1.5rem 0 0;
}

.viz-list li {
  margin-bottom: 1rem;
}

.viz-list a {
  color: var(--accent);
  text-decoration: none;
  font-weight: 500;
}

.viz-list a:hover {
  text-decoration: underline;
}

.viz-list small {
  display: block;
  color: var(--muted);
  font-size: 0.85rem;
}

footer {
  text-align: center;
  color: var(--muted);
  font-size: 0.85rem;
  margin-top: 3rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
}

.back-link {
  display: inline-block;
  margin-bottom: 1rem;
  color: var(--accent);
  text-decoration: none;
}

.back-link:hover {
  text-decoration: underline;
}
"""


def main() -> None:
    print("Building insights site...")
    build()
    print("Done.")


if __name__ == "__main__":
    main()
