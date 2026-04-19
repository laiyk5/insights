# Insights

A collection of data mining, statistical analysis, and visualization projects. Published as a static site via GitHub Pages.

## Project Structure

```text
insights/
├── site-builder/          # Static site generator
├── estate-investment/     # Subproject: 房价地图 (buy vs rent, rental yield)
└── docs/                  # GENERATED — GitHub Pages source
```

## Adding a New Subproject

To have a subproject automatically discovered and published:

1. **Create your subproject directory** at the repo root (e.g., `my-analysis/`).
2. **Generate HTML outputs** into `my-analysis/outputs/*.html`.
3. **Create `my-analysis/site-manifest.json`**:

   ```json
   {
     "name": "My Analysis",
     "description": "What this project does",
     "route": "my-analysis",
     "visualizations": [
       {
         "title": "Chart Title",
         "file": "chart.html",
         "description": "What this chart shows"
       }
     ]
   }
   ```

4. **(Optional)** Add `my-analysis/site-assets/` for thumbnails or custom CSS.

The site builder will auto-discover the manifest on the next build.

## Building the Site Locally

```bash
cd site-builder
uv sync
uv run python -m site_builder.builder
```

The generated site will be in `docs/`. Open `docs/index.html` to preview.

## Deployment

The repo is configured with a GitHub Actions workflow (`.github/workflows/deploy.yml`) that rebuilds `docs/` on every push to `main`.

To enable GitHub Pages:

1. Go to **Settings → Pages** in the GitHub repo.
2. Set **Source** to "Deploy from a branch".
3. Select the `main` branch and `/docs` folder.
4. Save.
