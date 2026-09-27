"""Milestone 2, step 2b: the per-pixel change map, 2019 -> 2026.

Every 10 m pixel's greenness change, made relative the same way the hex ranking
is (gotcha 8): each year's greenness minus that year's city-wide mean, where the
mean is taken over the hexes of the masked table, exactly as the notebooks
normalise. So averaging this image over any hex gives back that hex's
end-minus-start in `m2_hex_table_masked.csv`; `m2_change_map.ipynb` checks it.

Mapped water (the `--mask-water` polygons) is transparent, as it is in the table.
Outside the study boundary is transparent too.

The image is computed and rendered in Earth Engine; only the PNG comes down
(`getThumbURL`), at about 18 m a pixel: 3,000 px wide is over Earth Engine's
50 MB thumbnail limit. It is a picture for looking at, not data: the endpoint
rasters for the site are milestone 5's job. The per-pixel values stay
server-side, which is the whole point of the layered design in PROJECT.md.
"""

import os
import socket
import sys
import urllib.request
from pathlib import Path

import ee
import geopandas as gpd
import pandas as pd

from measure_hexes import MASKED_CLASSES, NET_TIMEOUT_S, WATER

START, END = 2019, 2026
DEADLINE_MS = 120_000
CHANGE_RANGE = 0.3
PALETTE = ["#543005", "#8c510a", "#bf812d", "#dfc27d", "#f6f6f6", "#80cdc1", "#35978f", "#01665e", "#003c30"]
WIDTH_PX = 2800
SIMPLIFY_DEG = 0.00005

TABLE = Path("results/m2_hex_table_masked.csv")
BOUNDARY = Path("data/study_boundary.geojson")
OUT = Path("results/m2_change_map.png")


def greenness(year: int, region) -> ee.Image:
	return (
		ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
		.filterBounds(region)
		.filterDate(f"{year}-02-01", f"{year}-03-31")
		.median()
		.normalizedDifference(["B8", "B4"])
	)


def change_image(region, year_mean: pd.Series, water) -> ee.Image:
	start = greenness(START, region).subtract(year_mean[START])
	end = greenness(END, region).subtract(year_mean[END])
	lakes = ee.FeatureCollection([ee.Feature(ee.Geometry(g.__geo_interface__)) for g in water.geometry])
	return end.subtract(start).updateMask(ee.Image.constant(1).paint(lakes, 0)).clip(region).rename("change")


def main() -> int:
	project = os.environ.get("EE_PROJECT")
	if not project:
		sys.exit("Set EE_PROJECT to your Google Cloud project id first.")
	socket.setdefaulttimeout(NET_TIMEOUT_S)
	ee.Initialize(project=project)
	ee.data.setDeadline(DEADLINE_MS)

	year_mean = pd.read_csv(TABLE).pivot(index="h3", columns="year", values="green").mean(axis=0)
	boundary = gpd.read_file(BOUNDARY).geometry.iloc[0]
	region = ee.Geometry(boundary.__geo_interface__)
	water = gpd.read_file(WATER)
	water = water[water["class"].isin(MASKED_CLASSES)]
	water = water.assign(geometry=water.geometry.simplify(SIMPLIFY_DEG))
	print(f"city-wide mean greenness {START} {year_mean[START]:.4f}, {END} {year_mean[END]:.4f}; "
		  f"masking {len(water):,} water polygons")

	image = change_image(region, year_mean, water).visualize(min=-CHANGE_RANGE, max=CHANGE_RANGE, palette=PALETTE)
	url = image.getThumbURL({"region": region, "dimensions": WIDTH_PX, "format": "png"})
	OUT.write_bytes(urllib.request.urlopen(url, timeout=NET_TIMEOUT_S).read())
	print(f"wrote {OUT} ({OUT.stat().st_size / 1e6:.1f} MB)")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
