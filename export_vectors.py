"""Milestone 5: the vector layers the site reads, written to `site/data/`.

Only what the M6 spec (PROJECT.md, 2026-09-29) puts on the page, and only losses:

  hexes.geojson     all 2,868 hexes; `loss` is how far greenness fell against the
                    city average 2019->2026 (positive = lost), null where it rose
                    or the hex has under 25% land after the lake mask, and null
                    where the photo check found lake works (not loss); `place`
                    when the hex belongs to a checked place; `doubtful` when the
                    photo check could not settle it
  places.geojson    one point per place: neighbouring checked hex losses merged
                    into one place, each checked lake-ring loss its own place,
                    with the plain copy from `site/places.csv` and the front it
                    sits on (north-west, east, or elsewhere)
  outlines.geojson  the shape to draw when a place is selected: the merged hexes,
                    or a lake's clean ring (the 10-30 m bands) and its water
  details.json      every checked loss for the method page's table
  boundary.geojson  the study boundary and the GBA outline

"Checked" means a photo-check verdict of real loss (M2: real loss or real loss on
wetland; M4: real loss). Lake works, doubtful places and gains are not exported.
Nothing here touches Earth Engine; `export_crops.py` makes the card photos.
"""

import csv
import json
from pathlib import Path

import geopandas as gpd
import h3
import pandas as pd
from shapely.geometry import Polygon, mapping, shape
from shapely.ops import unary_union

from measure_rings import BOUNDARY, METRIC, WATER, lakes, surroundings
from measure_ring_greenness import band_shapes

YEARS = (2019, 2026)
LAND_CUTOFF = 0.25
FULL_HEX_PIXELS = 8_004
REAL_HEX = ("real loss", "real loss, wetland")
REAL_RING = ("real loss",)
PRECISION = 5
RING_SIMPLIFY_M = 1

TABLE = Path("results/m2_hex_table_masked.csv")
HEX_VERDICTS = Path("results/m2_loss_verdicts.csv")
RING_VERDICTS = Path("results/m4_ring_verdicts.csv")
GRID = Path("data/hex_grid.geojson")
NAMES = Path("data/place_names.json")
COPY = Path("site/places.csv")
OUT = Path("site/data")
GBA_KEY = "lookup?osm_ids=R7902476&format=json&polygon_geojson=1"


def front(lon: float, lat: float) -> str:
	if 77.45 < lon < 77.6 and lat > 13.05:
		return "north-west"
	if lon >= 77.64 and lat > 12.9:
		return "east"
	return "elsewhere"


def rounded(geom) -> dict:
	def walk(v):
		return round(v, PRECISION) if isinstance(v, float) else [walk(x) for x in v]

	g = mapping(geom)
	return {"type": g["type"], "coordinates": walk(json.loads(json.dumps(g["coordinates"])))}


def feature(geom, **props) -> dict:
	return {"type": "Feature", "geometry": rounded(geom), "properties": props}


def write(name: str, features: list[dict]) -> None:
	path = OUT / name
	path.write_text(json.dumps({"type": "FeatureCollection", "features": features}, separators=(",", ":")))
	print(f"{path}: {len(features)} features, {path.stat().st_size / 1e3:.0f} kB")


def hex_polygon(cell: str) -> Polygon:
	return Polygon([(lon, lat) for lat, lon in h3.cell_to_boundary(cell)])


def clusters(cells: set[str]) -> list[list[str]]:
	left, out = set(cells), []
	while left:
		seed = left.pop()
		group, stack = {seed}, [seed]
		while stack:
			for n in h3.grid_disk(stack.pop(), 1):
				if n in left:
					left.remove(n)
					group.add(n)
					stack.append(n)
		out.append(sorted(group))
	return out


def main() -> int:
	OUT.mkdir(parents=True, exist_ok=True)
	copy = {r["key"]: r for r in csv.DictReader(COPY.open())}

	table = pd.read_csv(TABLE)
	green = table.pivot(index="h3", columns="year", values="green")
	land = table.pivot(index="h3", columns="year", values="n_pixels").min(axis=1) / FULL_HEX_PIXELS
	norm = green - green.mean(axis=0)
	change = (norm[YEARS[1]] - norm[YEARS[0]]).where(land >= LAND_CUTOFF)

	all_hex_v = pd.read_csv(HEX_VERDICTS).set_index("h3")
	hex_v = all_hex_v[all_hex_v.verdict.isin(REAL_HEX)]
	lake_works = set(all_hex_v.index[all_hex_v.verdict == "lake works"])
	doubtful = set(all_hex_v.index[all_hex_v.verdict == "doubtful"])
	ring_v = pd.read_csv(RING_VERDICTS)
	ring_v = ring_v[ring_v.verdict.isin(REAL_RING)].set_index("osm")

	places, outlines, details, member = [], [], [], {}
	for group in clusters(set(hex_v.index)):
		top = min(group, key=lambda c: hex_v.loc[c, "rank"])
		c = copy[top]
		for cell in group:
			member[cell] = c["id"]
		lats, lons = zip(*(h3.cell_to_latlng(cell) for cell in group))
		lon, lat = sum(lons) / len(lons), sum(lats) / len(lats)
		places.append(feature(shape({"type": "Point", "coordinates": [lon, lat]}), id=c["id"], kind="ground",
			name=c["name"], text=c["text"], fact=c["fact"] or None, front=front(lon, lat), hexes=len(group)))
		outlines.append(feature(unary_union([hex_polygon(cell) for cell in group]), id=c["id"], role="area"))
		for cell in group:
			r = hex_v.loc[cell]
			details.append({"place": c["id"], "name": c["name"], "kind": "ground", "rank": int(r["rank"]),
				"rank_from_2020": None if pd.isna(r.rank_from_2020) else int(r.rank_from_2020),
				"locality": r.locality, "note": r.note})

	boundary = gpd.read_file(BOUNDARY).to_crs(METRIC).union_all()
	water = gpd.read_file(WATER).to_crs(METRIC)
	water["geometry"] = water.geometry.make_valid()
	frame = lakes(water, boundary)
	frame = frame[frame.osm.isin(ring_v.index)]
	for lake, blockers, _ in surroundings(frame, water):
		c = copy[lake.osm]
		r = ring_v.loc[lake.osm]
		bands = band_shapes(lake.geometry, blockers)
		wgs = gpd.GeoSeries([lake.geometry, bands[1].union(bands[2]), lake.geometry.representative_point()],
			crs=METRIC).simplify(RING_SIMPLIFY_M).to_crs("EPSG:4326")
		point = wgs.iloc[2]
		places.append(feature(point, id=c["id"], kind="lake", name=c["name"], text=c["text"],
			fact=c["fact"] or None, front=front(point.x, point.y), hexes=0))
		outlines.append(feature(wgs.iloc[1], id=c["id"], role="ring"))
		outlines.append(feature(wgs.iloc[0], id=c["id"], role="water"))
		details.append({"place": c["id"], "name": c["name"], "kind": "lake", "rank": int(r["rank"]),
			"rank_from_2020": int(r.rank_from_2020), "locality": None, "note": r.note})

	unused = {r["id"] for r in copy.values()} - {p["properties"]["id"] for p in places}
	if unused:
		raise SystemExit(f"copy rows with no place: {sorted(unused)}")

	grid = gpd.read_file(GRID)
	hexes = [feature(g, h3=h, loss=None if h in lake_works or pd.isna(change.get(h)) or change[h] >= 0 else round(-change[h], 3),
		place=member.get(h), **({"doubtful": True} if h in doubtful else {})) for h, g in zip(grid.h3, grid.geometry)]

	gba = shape(json.loads(NAMES.read_text())[GBA_KEY][0]["geojson"])
	study = gpd.read_file(BOUNDARY).to_crs("EPSG:4326").union_all()

	write("hexes.geojson", hexes)
	write("places.geojson", places)
	write("outlines.geojson", outlines)
	write("boundary.geojson", [feature(study, role="study"), feature(gba, role="gba")])
	(OUT / "details.json").write_text(json.dumps(sorted(details, key=lambda d: (d["kind"], d["rank"])), indent=1))
	print(f"{OUT / 'details.json'}: {len(details)} rows")
	counts = pd.Series([p["properties"]["front"] for p in places]).value_counts().to_dict()
	print(f"{len(places)} places by front: {counts}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
