"""Milestone 1: ground-truth spot check.

Dry-season (Feb-Mar) median composite per year, sampled over OSM polygons for a
few places whose recent history we know first-hand, so a broken method has
something to visibly fail against.

Each site is probed with the index that can actually see the expected change:
  lalbagh                  NDVI   mature park            expect flat
  kaikondrahalli_lake      MNDWI  restored lake, water   expect flat-to-gain
  kaikondrahalli_rim_50    NDVI   its planted rim        expect gain
  kaikondrahalli_rim_100   NDVI   ditto, wider           expect gain, diluted
  kaikondrahalli_rim_200   NDVI   ditto, widest          expect gain, diluted
  varthur_built            NDVI   Varthur minus its lake expect clear loss

The rim is read at three radii rather than one: a gain that strengthens as the
ring narrows is dilution by whatever surrounds the lake, while a flat reading at
every radius says the restoration simply predates the window.

NDVI over open water is meaningless, which is why the lake is read in MNDWI and
its rim is a separate region.
"""

import csv
import json
import os
import sys
from pathlib import Path

import ee

COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
YEARS = list(range(2016, 2027))
SCALE_M = 10
RIMS = (50, 100, 200)
SITES = Path("data/osm_sites.geojson")
OUT = Path("results/m1_spot_check.csv")

PROBE = {
	"lalbagh": "ndvi",
	"kaikondrahalli_lake": "mndwi",
	**{f"kaikondrahalli_rim_{m}": "ndvi" for m in RIMS},
	"varthur_built": "ndvi",
}
EXPECTED = {
	"lalbagh": "flat",
	"kaikondrahalli_lake": "flat/gain",
	**{f"kaikondrahalli_rim_{m}": "gain" for m in RIMS},
	"varthur_built": "loss",
}


def regions() -> dict[str, ee.Geometry]:
	if not SITES.exists():
		sys.exit(f"{SITES} missing — run fetch_sites.py first.")
	raw = {f["properties"]["site"]: ee.Geometry(f["geometry"]) for f in json.loads(SITES.read_text())["features"]}
	lake = raw["kaikondrahalli_lake"]
	return {
		"lalbagh": raw["lalbagh"],
		"kaikondrahalli_lake": lake,
		**{f"kaikondrahalli_rim_{m}": lake.buffer(m).difference(lake, maxError=1) for m in RIMS},
		"varthur_built": raw["varthur_area"].difference(raw["varthur_lake"], maxError=1),
	}


def dry_season(year: int, region: ee.Geometry | ee.FeatureCollection) -> ee.ImageCollection:
	return (
		ee.ImageCollection(COLLECTION)
		.filterBounds(region)
		.filterDate(f"{year}-02-01", f"{year}-03-31")
	)


def indices(collection: ee.ImageCollection) -> ee.Image:
	composite = collection.median()
	ndvi = composite.normalizedDifference(["B8", "B4"]).rename("ndvi")
	mndwi = composite.normalizedDifference(["B3", "B11"]).rename("mndwi")
	return ndvi.addBands(mndwi)


def main() -> int:
	project = os.environ.get("EE_PROJECT")
	if not project:
		sys.exit("Set EE_PROJECT to your Google Cloud project id first.")

	ee.Initialize(project=project)
	by_site = regions()
	names = list(by_site)
	sites = ee.FeatureCollection([ee.Feature(by_site[n], {"site": n}) for n in names])

	counts = ee.List([
		ee.List([dry_season(y, by_site[n]).size() for n in names]) for y in YEARS
	]).getInfo()
	n_images = {(n, y): counts[i][j] for i, y in enumerate(YEARS) for j, n in enumerate(names)}

	print("scenes per site per dry season (Feb 1 - Mar 31):")
	print(f"  {'year':<6}" + "".join(f"{n[:19]:>21}" for n in names))
	for i, y in enumerate(YEARS):
		print(f"  {y:<6}" + "".join(f"{counts[i][j]:>21}" for j in range(len(names))))

	usable = [y for y in YEARS if any(n_images[(n, y)] > 0 for n in names)]
	if not usable:
		sys.exit("No usable years. Check the collection id or date windows.")

	stats = ee.FeatureCollection([
		indices(dry_season(y, sites))
		.reduceRegions(collection=sites, reducer=ee.Reducer.mean(), scale=SCALE_M)
		.map(lambda f, y=y: f.set("year", y))
		for y in usable
	]).flatten()

	rows = sorted(
		(
			{
				"site": p["site"],
				"probe": PROBE[p["site"]],
				"expected": EXPECTED[p["site"]],
				"year": p["year"],
				"n_images": n_images[(p["site"], p["year"])],
				"value": p.get(PROBE[p["site"]]),
				"ndvi": p.get("ndvi"),
				"mndwi": p.get("mndwi"),
			}
			for p in (f["properties"] for f in stats.getInfo()["features"])
		),
		key=lambda r: (names.index(r["site"]), r["year"]),
	)

	print(f"\n{'site':<22}{'probe':<7}{'expect':<11}{'year':<6}{'n':<4}{'value':>8}")
	last = None
	for r in rows:
		if r["site"] != last:
			print()
			last = r["site"]
		val = f"{r['value']:.3f}" if r["value"] is not None else "  --  "
		print(f"{r['site']:<22}{r['probe']:<7}{r['expected']:<11}{r['year']:<6}{r['n_images']:<4}{val:>8}")

	OUT.parent.mkdir(exist_ok=True)
	with OUT.open("w", newline="") as fh:
		writer = csv.DictWriter(fh, fieldnames=["site", "probe", "expected", "year", "n_images", "value", "ndvi", "mndwi"])
		writer.writeheader()
		writer.writerows(rows)
	print(f"\nwrote {OUT}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
