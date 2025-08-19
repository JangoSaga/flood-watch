# Screenshots Guide

Add screenshots here to illustrate the UI and API outputs.

## Suggested shots
- docs/screenshots/home.png — Homepage overview
- docs/screenshots/plots_map.png — Plots map with precipitation and predictions
- docs/screenshots/heatmap.png — Damage/risk heatmap
- docs/screenshots/city_forecast.png — City forecast view (e.g., Pune)
- docs/screenshots/health_check.png — /api/health response example

## How to capture
- Frontend: start from `frontend/floodguard/` with `npm run dev` and open `http://localhost:3000`
- Backend: run `python FloodML-master/app/app.py` and open `http://localhost:5000/api/health`
- Use consistent window sizes (e.g., 1440x900) for clean images

## Naming & format
- Prefer `.png`
- Kebab-case names (e.g., `city-forecast.png`)
- Avoid personally identifiable information

## Updating README
- After adding images, embed them in `README.md`, e.g.:

```markdown
![Plots Map](docs/screenshots/plots_map.png)
```
