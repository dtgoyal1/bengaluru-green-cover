"""Milestone 4, step 0: greenness per year in each 10 m band of each lake's ring.

The Earth Engine half of the gate. `measure_rings.py` counted the pixels; this
measures them, for the 590 OSM lakes of 1 ha or more (decided 2026-09-28), one
row per lake per band with the dry-season greenness of every year 2019-2026.

Each band is sent as a polygon: the ring cut back from other water, intersected
with the zone 0-10, 10-20 or 20-30 m from the lake. The reduction is pinned to
the Sentinel-2 grid (EPSG:32643, 10 m, edges on multiples of 10) and unweighted,
so a pixel is in a band exactly when its centre is, the rule `measure_rings.py`
counts by. `n_pixels` is Earth Engine's count; `local_px` is the same polygon
counted here. They must agree lake by lake, or the grid is not the one counted.

Composites are the Feb-Mar median with no cloud mask, the same as `measure_hexes.py`.
Values are absolute; normalise downstream with the masked hex table's yearly means.
"""

import os
import socket
import sys
import time
from pathlib import Path

import ee
import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

from measure_rings import BOUNDARY, METRIC, PIXEL_M, WATER, lakes, ring, surroundings

YEARS = list(range(2019, 2027))
MIN_HA = 1
BANDS = ("0_10", "10_20", "20_30")
QUAD_SEGS = 32
CHUNK = 150
MAX_TRIES = 4
NET_TIMEOUT_S = 300
GRID = {"crs": METRIC, "crsTransform": [PIXEL_M, 0, 0, 0, -PIXEL_M, 0]}
OUT = Path("results/m4_ring_table.csv")


def band_shapes(lake, blockers: list) -> list:
	zone = ring(lake, blockers)
	edges = [lake] + [lake.buffer(d, quad_segs=QUAD_SEGS) for d in (10, 20, 30)]
	return [zone.intersection(outer).difference(inner) for inner, outer in zip(edges, edges[1:])]


def centre_count(shape) -> int:
	if shape.is_empty:
		return 0
	minx, miny, maxx, maxy = shape.bounds
	xs = np.arange(np.floor(minx / PIXEL_M) * PIXEL_M + PIXEL_M / 2, maxx, PIXEL_M)
	ys = np.arange(np.floor(miny / PIXEL_M) * PIXEL_M + PIXEL_M / 2, maxy, PIXEL_M)
	x, y = (a.ravel() for a in np.meshgrid(xs, ys))
	return int(shapely.contains_xy(shape, x, y).sum())


def greenness() -> ee.Image:
	return ee.Image.cat([
		ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
		.filterDate(f"{y}-02-01", f"{y}-03-31")
		.median()
		.normalizedDifference(["B8", "B4"])
		.rename(f"g{y}")
		for y in YEARS
	])


def reduce(image: ee.Image, chunk: pd.DataFrame) -> list[dict]:
	wgs = gpd.GeoSeries(chunk.geometry.values, crs=METRIC).to_crs("EPSG:4326")
	fc = ee.FeatureCollection([
		ee.Feature(ee.Geometry(g.__geo_interface__, proj="EPSG:4326", geodesic=False), {"key": k})
		for g, k in zip(wgs, chunk.key)
	])
	reducer = ee.Reducer.mean().combine(ee.Reducer.count(), sharedInputs=True).unweighted()
	for attempt in range(MAX_TRIES):
		try:
			stats = image.reduceRegions(collection=fc, reducer=reducer, **GRID, tileScale=4)
			return [f["properties"] for f in stats.getInfo()["features"]]
		except Exception as exc:
			print(f"  attempt {attempt + 1} failed: {exc}")
			time.sleep(30)
	raise RuntimeError("Earth Engine unavailable")


def main() -> int:
	project = os.environ.get("EE_PROJECT")
	if not project:
		sys.exit("Set EE_PROJECT to your Google Cloud project id first.")
	socket.setdefaulttimeout(NET_TIMEOUT_S)
	ee.Initialize(project=project)

	boundary = gpd.read_file(BOUNDARY).to_crs(METRIC).union_all()
	water = gpd.read_file(WATER).to_crs(METRIC)
	water["geometry"] = water.geometry.make_valid()
	frame = lakes(water, boundary)
	frame = frame[frame.area >= MIN_HA * 1e4].reset_index(drop=True)

	rows = []
	for lake, blockers, _ in surroundings(frame, water):
		for band, shape in zip(BANDS, band_shapes(lake.geometry, blockers)):
			rows.append({"osm": lake.osm, "name": lake.name, "band": band, "key": f"{lake.osm}|{band}",
				"local_px": centre_count(shape), "geometry": shape})
	bands = gpd.GeoDataFrame(rows, crs=METRIC)
	bands = bands[bands.local_px > 0].reset_index(drop=True)
	print(f"{len(frame)} lakes, {len(bands)} bands, {bands.local_px.sum():,} pixels")

	image = greenness()
	measured = {}
	for i in range(0, len(bands), CHUNK):
		for p in reduce(image, bands.iloc[i : i + CHUNK]):
			measured[p["key"]] = p
		print(f"  {min(i + CHUNK, len(bands))}/{len(bands)}")

	out = bands.drop(columns=["geometry", "key"]).copy()
	props = [measured[k] for k in bands.key]
	out["n_pixels"] = [p.get("g2026_count") for p in props]
	for y in YEARS:
		out[f"green_{y}"] = [p.get(f"g{y}_mean") for p in props]
	out.to_csv(OUT, index=False)
	gap = (out.n_pixels - out.local_px).abs()
	print(f"wrote {OUT}; Earth Engine count equals the local count in {(gap == 0).mean():.1%} of bands, "
		f"largest gap {gap.max()} px")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
