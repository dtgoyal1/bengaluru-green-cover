"""Milestone 5: the before/after photos on each place's card, in `site/data/crops/`.

Cut straight from Earth Engine at the native 10 m, from the same single days as
the swipe (`export_tiles.DAYS`), with the place outlined: white round the merged
hexes of a ground place, a thin blue line round a lake's water so the ring
beside it stays visible. The mockup's first try cropped from the page-wide
picture and blew it up 2x, which showed nothing (logged 2026-09-29).

Reads `site/data/places.geojson` and `outlines.geojson`, so run `export_vectors.py` first.
"""

import json
import os
import socket
import sys
import urllib.request
from pathlib import Path

import ee
import geopandas as gpd
from shapely.geometry import shape

from export_tiles import DAYS, RGB_MAX
from measure_rings import BOUNDARY, METRIC

PAD_M = {"ground": 400, "lake": 650}
LINE = {"area": ("#ffffff", 1), "water": ("#7fd3ff", 1)}
NET_TIMEOUT_S = 120

DATA = Path("site/data")
OUT = DATA / "crops"


def square(geom, pad_m: float):
	metric = gpd.GeoSeries([geom], crs="EPSG:4326").to_crs(METRIC).iloc[0]
	w, s, e, n = metric.bounds
	half = max(e - w, n - s) / 2 + pad_m
	cx, cy = (w + e) / 2, (s + n) / 2
	return ee.Geometry.Rectangle([cx - half, cy - half, cx + half, cy + half], proj=METRIC, geodesic=False)


def main() -> int:
	project = os.environ.get("EE_PROJECT")
	if not project:
		sys.exit("Set EE_PROJECT to your Google Cloud project id first.")
	socket.setdefaulttimeout(NET_TIMEOUT_S)
	ee.Initialize(project=project)
	OUT.mkdir(parents=True, exist_ok=True)

	places = json.loads((DATA / "places.geojson").read_text())["features"]
	outlines = json.loads((DATA / "outlines.geojson").read_text())["features"]
	area = ee.Geometry.Rectangle(list(gpd.read_file(BOUNDARY).to_crs("EPSG:4326").total_bounds))
	photos = {
		year: ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(area)
		.filter(ee.Filter.stringStartsWith("system:index", day)).mosaic()
		.visualize(bands=["B4", "B3", "B2"], min=0, max=RGB_MAX)
		for year, day in DAYS.items()
	}
	for place in places:
		pid, kind = place["properties"]["id"], place["properties"]["kind"]
		shapes = [o for o in outlines if o["properties"]["id"] == pid and o["properties"]["role"] in LINE]
		region = square(shape(shapes[0]["geometry"]), PAD_M[kind])
		colour, width = LINE[shapes[0]["properties"]["role"]]
		edge = ee.FeatureCollection([ee.Feature(ee.Geometry(o["geometry"])) for o in shapes])
		line = ee.Image().byte().paint(edge, 1, width).selfMask().visualize(palette=[colour])
		for year, image in photos.items():
			url = image.blend(line).getThumbURL({"region": region, "crs": METRIC, "scale": 10, "format": "jpg"})
			urllib.request.urlretrieve(url, OUT / f"{pid}_{year}.jpg")
		print(f"{pid:32} done")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
