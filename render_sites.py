"""Render the imagery behind the milestone 1 numbers, one frame per site per year.

The point is to make the numbers falsifiable by eye: each frame is the exact
dry-season median composite that `spot_check.py` averaged, over the exact
geometry it averaged, with that geometry outlined.

Two frames per site per year:
  *_rgb.jpg    true colour, fixed stretch, so years are comparable by eye
  *_ndvi.png   the greenness band, fixed palette, same stretch

Outlines matter. `varthur_built` is the Varthur area MINUS Varthur lake, so the
lake is drawn separately in red as excluded — an image dominated by open water
does not otherwise reconcile with a greenness of 0.21.

No cloud masking anywhere, deliberately: this mirrors `spot_check.py`, which has
none either. At 12+ scenes the median absorbs cloud; at the 2-4 scenes of
2017-2018 it does not, and these frames are how you see that.
"""

import json
import os
import sys
import urllib.request
from pathlib import Path

import ee

COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
YEARS = list(range(2016, 2027))
SITES = Path("data/osm_sites.geojson")
OUT = Path("results/imagery")

RGB_MAX = 3000
NDVI_RANGE = (-0.2, 0.8)
NDVI_PALETTE = ["#8c510a", "#d8b365", "#f6e8c3", "#c7eae5", "#5ab4ac", "#01665e"]


def outline(geom: ee.Geometry, colour: str, width: int) -> ee.Image:
	painted = ee.Image().byte().paint(ee.FeatureCollection([ee.Feature(geom)]), 1, width)
	return painted.selfMask().visualize(palette=[colour])


def fetch(image: ee.Image, box: ee.Geometry, path: Path, px: int, fmt: str) -> None:
	url = image.getThumbURL({"region": box, "dimensions": px, "format": fmt})
	urllib.request.urlretrieve(url, path)


def main() -> int:
	project = os.environ.get("EE_PROJECT")
	if not project:
		sys.exit("Set EE_PROJECT to your Google Cloud project id first.")
	ee.Initialize(project=project)

	raw = {f["properties"]["site"]: ee.Geometry(f["geometry"]) for f in json.loads(SITES.read_text())["features"]}
	varthur_built = raw["varthur_area"].difference(raw["varthur_lake"], maxError=1)

	# site -> (measured geometry, display box, overlay outlines, thumbnail width)
	views = {
		"varthur_built": (
			varthur_built,
			raw["varthur_area"].bounds(),
			[(raw["varthur_area"], "#ffe600", 2), (raw["varthur_lake"], "#ff2d2d", 2)],
			700,
		),
		"lalbagh": (
			raw["lalbagh"],
			raw["lalbagh"].buffer(300).bounds(),
			[(raw["lalbagh"], "#ffe600", 2)],
			420,
		),
	}

	OUT.mkdir(parents=True, exist_ok=True)
	manifest = []

	for site, (measured, box, overlays, px) in views.items():
		for year in YEARS:
			col = (
				ee.ImageCollection(COLLECTION)
				.filterBounds(box)
				.filterDate(f"{year}-02-01", f"{year}-03-31")
			)
			n, clouds = col.size().getInfo(), col.aggregate_array("CLOUDY_PIXEL_PERCENTAGE").getInfo()
			if n == 0:
				print(f"{site:<16}{year}  no scenes — skipped")
				manifest.append({"site": site, "year": year, "n": 0, "clouds": [], "rgb": None, "ndvi": None})
				continue

			composite = col.median()
			edges = [outline(g, c, w) for g, c, w in overlays]

			rgb = composite.visualize(bands=["B4", "B3", "B2"], min=0, max=RGB_MAX)
			ndvi = composite.normalizedDifference(["B8", "B4"]).visualize(
				min=NDVI_RANGE[0], max=NDVI_RANGE[1], palette=NDVI_PALETTE
			)
			for img in edges:
				rgb, ndvi = rgb.blend(img), ndvi.blend(img)

			rgb_path, ndvi_path = OUT / f"{site}_{year}_rgb.jpg", OUT / f"{site}_{year}_ndvi.png"
			fetch(rgb, box, rgb_path, px, "jpg")
			fetch(ndvi, box, ndvi_path, px, "png")
			mean_cloud = sum(clouds) / len(clouds) if clouds else None
			print(
				f"{site:<16}{year}  n={n:<3} mean cloud {mean_cloud:5.1f}%  "
				f"max {max(clouds):5.1f}%  {rgb_path.stat().st_size // 1024:>4}KB"
			)
			manifest.append({
				"site": site, "year": year, "n": n, "clouds": clouds,
				"rgb": rgb_path.name, "ndvi": ndvi_path.name,
			})

	(OUT / "manifest.json").write_text(json.dumps(manifest, indent=1))
	print(f"\nwrote {len(manifest)} entries to {OUT / 'manifest.json'}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
