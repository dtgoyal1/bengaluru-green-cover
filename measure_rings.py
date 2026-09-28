"""Milestone 4, step 0: how many 10 m pixels fit inside each lake's 30 m buffer.

The feasibility gate, run before any intersection is built. RMP-2015 protects a
30 m ring around every lake (decided 2026-09-28: measure against the old widths).
At 10 m that is three pixels across, and the first of them straddles a shoreline
that moves with the seasons and an OSM outline with its own error. So the ring
is counted in three 10 m bands by distance from the lake's own outline, and only
the outer two (10-30 m) count as clean.

Pixels are the Sentinel-2 grid in EPSG:32643: edges on multiples of 10 m, a pixel
counted by its centre. Rings are cut back where they run into other mapped water
(a lake, reservoir or sewage pond from `fetch_water.py`); wetland is land here, as
it is in the masked table, and is counted separately.

A lake is one OSM water/reservoir element, merged with any element it touches:
OSM maps one tank as several touching ways, and maps Bellandur and Varthur each as
one relation in several disjoint pieces, which must stay one lake. Only lakes
whose centre is inside the study boundary are counted. Nothing here touches
Earth Engine.
"""

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from shapely.strtree import STRtree

METRIC = "EPSG:32643"
PIXEL_M = 10
BUFFER_M = 30
LAKE_CLASSES = ("water", "reservoir")
MASKED_CLASSES = ("water", "reservoir", "wastewater")

BOUNDARY = Path("data/study_boundary.geojson")
WATER = Path("data/osm_water.geojson")
OUT = Path("results/m4_ring_pixels.csv")


def lakes(water: gpd.GeoDataFrame, boundary) -> gpd.GeoDataFrame:
	polys = water[water["class"].isin(LAKE_CLASSES)].dissolve("osm", as_index=False, aggfunc="first")
	geoms = polys.geometry.values
	parent = list(range(len(geoms)))

	def root(i: int) -> int:
		while parent[i] != i:
			parent[i] = parent[parent[i]]
			i = parent[i]
		return i

	for a, b in zip(*STRtree(geoms).query(geoms, predicate="intersects")):
		parent[root(a)] = root(b)
	merged = polys.assign(lake=[root(i) for i in range(len(geoms))]).dissolve("lake", aggfunc={
		"osm": lambda s: ";".join(sorted(s)),
		"name": lambda s: next((n for n in s if n), ""),
	}).reset_index(drop=True)
	return merged[merged.representative_point().within(boundary)].reset_index(drop=True)


def ring(lake, blockers: list):
	zone = lake.buffer(BUFFER_M).difference(lake)
	for other in blockers:
		zone = zone.difference(other)
	return zone


def surroundings(frame: gpd.GeoDataFrame, water: gpd.GeoDataFrame):
	masked = water[water["class"].isin(MASKED_CLASSES)].geometry.values
	wetland = water[water["class"] == "wetland"].geometry.values
	masked_tree, wetland_tree = STRtree(masked), STRtree(wetland)
	for lake in frame.itertuples():
		zone = lake.geometry.buffer(BUFFER_M)
		blockers = [g for g in masked[masked_tree.query(zone, predicate="intersects")]
			if not g.intersection(lake.geometry).area > 0]
		yield lake, blockers, list(wetland[wetland_tree.query(zone, predicate="intersects")])


def ring_pixels(lake, blockers: list, wetlands: list) -> dict:
	zone = ring(lake, blockers)
	minx, miny, maxx, maxy = zone.bounds
	xs = np.arange(np.floor(minx / PIXEL_M) * PIXEL_M + PIXEL_M / 2, maxx, PIXEL_M)
	ys = np.arange(np.floor(miny / PIXEL_M) * PIXEL_M + PIXEL_M / 2, maxy, PIXEL_M)
	x, y = (a.ravel() for a in np.meshgrid(xs, ys))
	inside = shapely.contains_xy(zone, x, y)
	x, y = x[inside], y[inside]
	dist = shapely.distance(lake.boundary, shapely.points(x, y))
	clean = dist >= PIXEL_M
	wet = np.zeros(len(x), bool)
	for patch in wetlands:
		wet |= shapely.contains_xy(patch, x, y)
	return {
		"px_0_10": int((dist < 10).sum()),
		"px_10_20": int(((dist >= 10) & (dist < 20)).sum()),
		"px_20_30": int((dist >= 20).sum()),
		"clean_px": int(clean.sum()),
		"clean_wetland_px": int((clean & wet).sum()),
	}


def main() -> int:
	boundary = gpd.read_file(BOUNDARY).to_crs(METRIC).union_all()
	water = gpd.read_file(WATER).to_crs(METRIC)
	water["geometry"] = water.geometry.make_valid()
	rows = []
	for lake, blockers, wetlands in surroundings(lakes(water, boundary), water):
		rows.append({
			"osm": lake.osm,
			"name": lake.name,
			"ha": round(lake.geometry.area / 1e4, 3),
			"perimeter_m": round(lake.geometry.length),
			**ring_pixels(lake.geometry, blockers, wetlands),
		})

	table = pd.DataFrame(rows).sort_values("ha", ascending=False)
	OUT.parent.mkdir(exist_ok=True)
	table.to_csv(OUT, index=False)
	print(f"wrote {OUT} — {len(table):,} lakes")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
