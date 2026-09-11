"""Milestone 2, step 1: the hex table.

Dry-season (Feb-Mar) median composite per year, greenness and wetness per pixel,
averaged into the H3 res-8 hexes from build_grid.py. One row per (hex, year).

The composite is NOT clipped to the study boundary, and does not need to be:
reduceRegions only ever reads inside a hex. The boundary's job was to decide
which hexes exist (build_grid.py, by hex centre); each of those is then measured
in full. So the effective study area is the union of the hexes (2,173 km2), very
slightly different from the buffered boundary (2,175 km2), and no hex is
partially covered.

This is the only thing that leaves Earth Engine. The per-pixel layers behind it
are ~22M values a year and stay server-side.

Values are stored ABSOLUTE, deliberately. Gotcha 8 forces the eventual *change
layer* to be relative — each hex against the city-wide median for its year — but
storing relative values would bake that choice in and make the table
un-re-derivable. Do the differencing downstream, from this CSV.

`n_pixels` is the data-quality column. Measured range is 7,966-8,042 with a
median of 8,004 — about 5% above the 7,580 implied by a 0.758 km2 hex at 10m,
which is projection differences between EPSG:32643 and what Earth Engine reduces
in, not an error. What matters is that it is near-constant: a hex whose count
collapses in one year but not others has a cloud gap, and comparing years for
that hex compares different ground — the failure that makes 2016 unusable at M1.
On the 2019-2026 run, zero hexes vary by more than 5% across years.

Two things learned the hard way on the first run, which hung after 2.5 years:

  * The Earth Engine client sets no socket timeout, so a dropped connection
    blocks forever. The retry below never fired because a hang raises nothing.
    `socket.setdefaulttimeout` converts it into an exception the retry can see.
  * The run is therefore resumable. Completed chunks are skipped on restart, so
    killing this script costs at most one chunk.
"""

import csv
import os
import socket
import sys
import time
from pathlib import Path

import ee
import geopandas as gpd

YEARS = list(range(2019, 2027))
CHUNK = 800
SCALE_M = 10
TILE_SCALE = 4
MAX_TRIES = 4
NET_TIMEOUT_S = 180
FULL_HEX_PIXELS = 8_004  # measured median, not derived

GRID = Path("data/hex_grid.geojson")
OUT = Path("results/m2_hex_table.csv")
FIELDS = ["h3", "year", "green", "wet", "n_pixels"]


def indices(year: int, region) -> ee.Image:
	composite = (
		ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
		.filterBounds(region)
		.filterDate(f"{year}-02-01", f"{year}-03-31")
		.median()
	)
	return (
		composite.normalizedDifference(["B8", "B4"]).rename("green")
		.addBands(composite.normalizedDifference(["B3", "B11"]).rename("wet"))
	)


def chunk_rows(frame, year: int) -> list[dict]:
	fc = ee.FeatureCollection([
		ee.Feature(ee.Geometry(r.geometry.__geo_interface__), {"h3": r.h3}) for r in frame.itertuples()
	])
	reducer = ee.Reducer.mean().combine(ee.Reducer.count(), sharedInputs=True)
	stats = (
		indices(year, fc)
		.reduceRegions(collection=fc, reducer=reducer, scale=SCALE_M, tileScale=TILE_SCALE)
		.select(["h3", "green_mean", "wet_mean", "green_count"], None, False)
	)
	return [
		{
			"h3": p["h3"],
			"year": year,
			"green": p.get("green_mean"),
			"wet": p.get("wet_mean"),
			"n_pixels": p.get("green_count"),
		}
		for p in (f["properties"] for f in stats.getInfo()["features"])
	]


def already_done() -> set[tuple[str, int]]:
	if not OUT.exists():
		return set()
	with OUT.open(newline="") as fh:
		return {(r["h3"], int(r["year"])) for r in csv.DictReader(fh) if r.get("green") not in (None, "")}


def main() -> int:
	project = os.environ.get("EE_PROJECT")
	if not project:
		sys.exit("Set EE_PROJECT to your Google Cloud project id first.")
	socket.setdefaulttimeout(NET_TIMEOUT_S)
	ee.Initialize(project=project)

	hexes = gpd.read_file(GRID)
	chunks = [hexes.iloc[i : i + CHUNK] for i in range(0, len(hexes), CHUNK)]
	done = already_done()
	print(f"{len(hexes):,} hexes x {len(YEARS)} years in {len(chunks)} chunks of <={CHUNK}")
	print(f"{len(done):,} rows already present — those chunks will be skipped\n")

	OUT.parent.mkdir(exist_ok=True)
	fresh = not OUT.exists()
	# append, and skip whole completed chunks: killing this script costs at most one chunk
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
						rows = chunk_rows(frame, year)
						break
					except Exception as exc:  # hangs surface here too, via the socket timeout
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
