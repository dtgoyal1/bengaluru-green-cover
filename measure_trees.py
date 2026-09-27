"""Milestone 2, second method: tree cover per hex from Google Dynamic World.

Greenness can't tell trees from crops, grass or scrub (gotcha 3). Dynamic World
labels every 10 m pixel; this keeps only its "trees" class. For each hex and year,
the Feb-Mar label is the most common one across that season's images (the notebook
showed mode and mean-probability agree to 0.6 points), and the hex's tree share is
the fraction of its pixels labelled trees. Same hexes, same years, same season as
`measure_hexes.py`, so the two tables join one-to-one on (h3, year).

One pass writes both readings:

  * `trees_land` / `n_land` — the default. OSM lakes, reservoirs and sewage ponds are
    masked, the exact polygons `measure_hexes.py --mask-water` uses, so the masked
    greenness table and this one measure the same ground. Wetlands are kept.
  * `trees_all` / `n_all` — no mask. Kept to test whether Dynamic World needs the mask
    at all: a reservoir refilling over a vegetated dry bed (Hesaraghatta 2022-23) can
    read as tree loss.

The counts are the data-quality columns, as `n_pixels` is for greenness: Dynamic
World only exists where Sentinel-2 had a usable scene, so a hex whose count drops in
one year is comparing different ground.

Resumable in the same way as `measure_hexes.py`. Also sets an Earth Engine request
deadline, which that script predates (see the 2026-09-23 log).
"""

import csv
import os
import socket
import sys
import time
from pathlib import Path

import ee
import geopandas as gpd

from measure_hexes import CHUNK, GRID, MASKED_CLASSES, MAX_TRIES, NET_TIMEOUT_S, SCALE_M, TILE_SCALE, WATER, YEARS
from measure_hexes import land_mask

TREES = 1
DEADLINE_MS = 120_000

OUT = Path("results/m2_hex_trees.csv")
FIELDS = ["h3", "year", "trees_land", "n_land", "trees_all", "n_all"]


def tree_bands(year: int, region, mask) -> ee.Image:
	label = (
		ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
		.filterBounds(region)
		.filterDate(f"{year}-02-01", f"{year}-03-31")
		.select("label")
		.mode()
	)
	trees = label.eq(TREES)
	on_land = trees.updateMask(mask) if mask is not None else trees
	return trees.rename("all").addBands(on_land.rename("land"))


def chunk_rows(frame, year: int, water) -> list[dict]:
	fc = ee.FeatureCollection([
		ee.Feature(ee.Geometry(r.geometry.__geo_interface__), {"h3": r.h3}) for r in frame.itertuples()
	])
	image = tree_bands(year, fc, land_mask(frame, water))
	reducer = ee.Reducer.mean().combine(ee.Reducer.count(), sharedInputs=True)
	stats = (
		image
		.reduceRegions(collection=fc, reducer=reducer, scale=SCALE_M, tileScale=TILE_SCALE)
		.select(["h3", "land_mean", "land_count", "all_mean", "all_count"], None, False)
	)
	return [
		{
			"h3": p["h3"],
			"year": year,
			"trees_land": p.get("land_mean"),
			"n_land": p.get("land_count"),
			"trees_all": p.get("all_mean"),
			"n_all": p.get("all_count"),
		}
		for p in (f["properties"] for f in stats.getInfo()["features"])
	]


def already_done() -> set[tuple[str, int]]:
	if not OUT.exists():
		return set()
	with OUT.open(newline="") as fh:
		return {(r["h3"], int(r["year"])) for r in csv.DictReader(fh) if r.get("n_all") not in (None, "")}


def main() -> int:
	project = os.environ.get("EE_PROJECT")
	if not project:
		sys.exit("Set EE_PROJECT to your Google Cloud project id first.")
	socket.setdefaulttimeout(NET_TIMEOUT_S)
	ee.Initialize(project=project)
	ee.data.setDeadline(DEADLINE_MS)

	hexes = gpd.read_file(GRID)
	water = gpd.read_file(WATER)
	water = water[water["class"].isin(MASKED_CLASSES)].to_crs(hexes.crs)
	chunks = [hexes.iloc[i : i + CHUNK] for i in range(0, len(hexes), CHUNK)]
	done = already_done()
	print(f"{len(hexes):,} hexes x {len(YEARS)} years in {len(chunks)} chunks of <={CHUNK} -> {OUT}")
	print(f"{len(done):,} rows already present — those chunks will be skipped\n")

	OUT.parent.mkdir(exist_ok=True)
	fresh = not OUT.exists()
	with OUT.open("a", newline="") as fh:
		writer = csv.DictWriter(fh, fieldnames=FIELDS)
		if fresh:
			writer.writeheader()
		added = 0
		for year in YEARS:
			started, skipped = time.time(), 0
			for i, frame in enumerate(chunks, 1):
				if all((h, year) in done for h in frame["h3"]):
					skipped += 1
					continue
				for attempt in range(1, MAX_TRIES + 1):
					try:
						rows = chunk_rows(frame, year, water)
						break
					except Exception as exc:
						if attempt == MAX_TRIES:
							raise
						print(f"  {year} chunk {i} attempt {attempt} failed ({type(exc).__name__}: {exc}); retrying")
						time.sleep(5 * attempt)
				writer.writerows(rows)
				fh.flush()
				added += len(rows)
			note = f" ({skipped}/{len(chunks)} chunks already done)" if skipped else ""
			print(f"  {year}  {time.time() - started:5.1f}s  +{added:>6,} new rows{note}")

	print(f"\nwrote {OUT} — {added:,} rows added")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
