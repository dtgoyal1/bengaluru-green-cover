"""Milestone 4, step 1: the evidence for photo-checking the 40 biggest ring losses.

The list is fixed by `notebooks/m4_ring_gate.ipynb`: the 40 lakes whose clean ring (10-30 m)
lost the most normalised greenness 2019 to 2026, readable or not. For each one this writes:

  * `results/m4_ring_evidence.csv` — the share of the clean ring's pixels that read as open water
    (MNDWI > 0, counted per pixel on the pinned grid) in every dry season, and the lake's rank if
    the change is measured from 2020 instead of 2019. Water rising into the ring turns grass or
    weed into water and reads as greenness loss: M2's top four losses were exactly that.
  * `results/m4_ring_photos/` — per lake, an Esri high-resolution photo with the lake (yellow) and
    the outer edge of the 30 m ring (cyan), and Sentinel-2 true colour for the eight dry seasons
    with the same outlines. The Esri frames are for looking at, not for publishing.

Resumable: frames already on disk are not fetched again. Lakes are fetched eight at a time.
"""

import os
import socket
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import ee
import geopandas as gpd
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw

from measure_ring_greenness import GRID, band_shapes
from measure_rings import BOUNDARY, BUFFER_M, METRIC, WATER, lakes, surroundings

TOP = 40
YEARS = list(range(2019, 2027))
CLEAN = ("10_20", "20_30")
FRAME_PAD_M = 60
ESRI_PX = 480
S2_PX = 240
RGB_MAX = 3000
NET_TIMEOUT_S = 300
WORKERS = 8
ESRI = "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"

LAKES = Path("results/m4_ring_lakes.csv")
TABLE = Path("results/m4_ring_table.csv")
HEX_TABLE = Path("results/m2_hex_table_masked.csv")
OUT = Path("results/m4_ring_evidence.csv")
PHOTOS = Path("results/m4_ring_photos")


def clean_series(table: pd.DataFrame, year_mean: pd.Series) -> pd.DataFrame:
	clean = table[table.band.isin(CLEAN)]
	cols = [f"green_{y}" for y in YEARS]
	weighted = clean[cols].mul(clean.n_pixels, axis=0).groupby(clean.osm).sum()
	series = weighted.div(clean.groupby("osm").n_pixels.sum(), axis=0)
	series.columns = YEARS
	return series - year_mean[YEARS].to_numpy()


def composite(year: int, region) -> ee.Image:
	return (
		ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(region)
		.filterDate(f"{year}-02-01", f"{year}-03-31").median()
	)


def to_ee(geom) -> ee.Geometry:
	wgs = gpd.GeoSeries([geom], crs=METRIC).to_crs("EPSG:4326")[0]
	return ee.Geometry(wgs.__geo_interface__, proj="EPSG:4326", geodesic=False)


def water_shares(clean_ring) -> dict[int, float]:
	region = to_ee(clean_ring)
	shares = ee.List([
		composite(y, region).normalizedDifference(["B3", "B11"]).gt(0)
		.reduceRegion(ee.Reducer.mean().unweighted(), region, **GRID).values().get(0)
		for y in YEARS
	]).getInfo()
	return dict(zip(YEARS, shares))


def esri_frame(box, shapes: list[tuple], path: Path) -> None:
	w, s, e, n = box
	query = urllib.parse.urlencode({
		"bbox": f"{w},{s},{e},{n}", "bboxSR": 4326, "imageSR": 4326,
		"size": f"{ESRI_PX},{ESRI_PX}", "format": "jpg", "f": "image",
	})
	urllib.request.urlretrieve(f"{ESRI}?{query}", path)
	image = Image.open(path).convert("RGB")
	draw = ImageDraw.Draw(image)
	for geom, colour in shapes:
		for part in getattr(geom, "geoms", [geom]):
			for line in [part.exterior, *part.interiors]:
				pts = [((x - w) / (e - w) * ESRI_PX, (n - y) / (n - s) * ESRI_PX) for x, y in line.coords]
				draw.line(pts, fill=colour, width=2)
	image.save(path, quality=88)


def s2_frame(year: int, box, outlines: list[tuple], path: Path) -> None:
	region = ee.Geometry.Rectangle(list(box))
	image = composite(year, region).visualize(bands=["B4", "B3", "B2"], min=0, max=RGB_MAX)
	for geom, colour in outlines:
		edge = ee.Image().byte().paint(ee.FeatureCollection([ee.Feature(geom)]), 1, 1)
		image = image.blend(edge.selfMask().visualize(palette=[colour]))
	url = image.getThumbURL({"region": region, "dimensions": S2_PX, "format": "jpg"})
	urllib.request.urlretrieve(url, path)


def main() -> int:
	project = os.environ.get("EE_PROJECT")
	if not project:
		sys.exit("Set EE_PROJECT to your Google Cloud project id first.")
	socket.setdefaulttimeout(NET_TIMEOUT_S)
	ee.Initialize(project=project)

	year_mean = pd.read_csv(HEX_TABLE).pivot(index="h3", columns="year", values="green").mean(axis=0)
	norm = clean_series(pd.read_csv(TABLE), year_mean)
	rank_2020 = (norm[2026] - norm[2020]).rank(method="first").astype(int)
	top = pd.read_csv(LAKES).sort_values("change").head(TOP).reset_index(drop=True)
	top["rank"] = range(1, TOP + 1)

	boundary = gpd.read_file(BOUNDARY).to_crs(METRIC).union_all()
	water = gpd.read_file(WATER).to_crs(METRIC)
	water["geometry"] = water.geometry.make_valid()
	frame = lakes(water, boundary)
	frame = frame[frame.osm.isin(top.osm)]

	PHOTOS.mkdir(parents=True, exist_ok=True)
	rows = {}
	with ThreadPoolExecutor(WORKERS) as pool:
		for osm, row in pool.map(lambda args: evidence_for(*args), surroundings(frame, water)):
			rows[osm] = row
			print(f"{osm:<36} water 2019 {row['ring_water_2019']:.0%} 2026 {row['ring_water_2026']:.0%}")

	evidence = top.join(pd.DataFrame.from_dict(rows, orient="index"), on="osm")
	evidence["rank_from_2020"] = evidence.osm.map(rank_2020)
	evidence.to_csv(OUT, index=False)
	print(f"wrote {OUT} and {PHOTOS}/")
	return 0


def evidence_for(lake, blockers: list, _) -> tuple[str, dict]:
	key = lake.osm.replace(";", "_")
	bands = dict(zip(("0_10", *CLEAN), band_shapes(lake.geometry, blockers)))
	clean_ring = bands["10_20"].union(bands["20_30"])
	outer = lake.geometry.buffer(BUFFER_M)
	box = gpd.GeoSeries([outer.buffer(FRAME_PAD_M).envelope], crs=METRIC).to_crs("EPSG:4326").total_bounds
	wgs = gpd.GeoSeries([lake.geometry, outer], crs=METRIC).to_crs("EPSG:4326")
	if not (PHOTOS / f"{key}_esri.jpg").exists():
		esri_frame(box, [(wgs[0], (255, 230, 0)), (wgs[1], (0, 230, 255))], PHOTOS / f"{key}_esri.jpg")
	outlines = [(to_ee(lake.geometry), "#ffe600"), (to_ee(outer), "#00e6ff")]
	for year in YEARS:
		if not (PHOTOS / f"{key}_{year}.jpg").exists():
			s2_frame(year, box, outlines, PHOTOS / f"{key}_{year}.jpg")
	shares = water_shares(clean_ring)
	return lake.osm, {"key": key,
		**{f"ring_water_{y}": round(v, 3) if v is not None else np.nan for y, v in shares.items()}}


if __name__ == "__main__":
	raise SystemExit(main())
