"""Milestone 2, step 0: the study boundary and the H3 hex grid laid over it.

Nothing in M2 can be measured before this exists — the boundary is the clip mask
for all eight years and the hexes are the reporting unit.

Boundary is the Greater Bengaluru Authority outer boundary plus a ~10km ring.
GBA alone stops short of Whitefield / Sarjapur / North Bangalore, where most of
the change is. The ring is a boundary we define, so it must be stated explicitly
when publishing.

Two conventions worth not rediscovering:

  * Areas and buffers are computed in EPSG:32643 (UTM 43N), never in degrees.
    Getting this wrong silently produces plausible-looking garbage.
  * A hex belongs to the grid if its CENTRE falls inside the boundary, which is
    what h3.geo_to_cells does. Hexes therefore straddle the edge, and that is
    deliberate: the 10km ring is self-defined, so its edge carries no meaning,
    and clipping hexes to it would leave edge hexes with fewer pixels than the
    rest for no gain. Do not "fix" this by clipping.
"""

import json
import urllib.parse
import urllib.request
from pathlib import Path

import geopandas as gpd
import h3
from shapely.geometry import Polygon, shape

UA = "bangalore-blue-green/0.1 (personal research)"
GBA_OSM_ID = "R7902476"          # boundary/administrative, admin_level 7, operator=Greater Bengaluru Authority
GBA_AREA_KM2 = (650, 800)        # sanity window: the GBA is ~712-717 km2
RING_M = 10_000
SIMPLIFY_M = 10                  # one Sentinel-2 pixel; the ring is arbitrary so this costs nothing
H3_RES = 8                       # ~0.74 km2, i.e. the "~1km hex" the project specifies
EXPECTED_HEXES = (2000, 4500)

METRIC = "EPSG:32643"
OUT_BOUNDARY = Path("data/study_boundary.geojson")
OUT_HEXES = Path("data/hex_grid.geojson")


def fetch_gba() -> Polygon:
	url = "https://nominatim.openstreetmap.org/lookup?" + urllib.parse.urlencode(
		{"osm_ids": GBA_OSM_ID, "format": "json", "polygon_geojson": 1}
	)
	hit = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=90))[0]
	geom = shape(hit["geojson"])
	area = gpd.GeoSeries([geom], crs="EPSG:4326").to_crs(METRIC).area.iloc[0] / 1e6
	if not GBA_AREA_KM2[0] <= area <= GBA_AREA_KM2[1]:
		raise SystemExit(f"{GBA_OSM_ID} is {area:,.1f} km2, outside the expected {GBA_AREA_KM2} — has OSM changed?")
	print(f"GBA boundary  {GBA_OSM_ID}  {area:,.1f} km2  ({hit['display_name'][:44]})")
	return geom


def main() -> int:
	gba = gpd.GeoSeries([fetch_gba()], crs="EPSG:4326").to_crs(METRIC)

	ringed = gba.buffer(RING_M)
	before = len(ringed.iloc[0].exterior.coords)
	study = ringed.simplify(SIMPLIFY_M)
	after = len(study.iloc[0].exterior.coords)
	area = study.area.iloc[0] / 1e6
	print(f"+{RING_M // 1000}km ring   {area:,.1f} km2   outline {before:,} -> {after:,} vertices "
	      f"(simplified at {SIMPLIFY_M}m)")

	study_wgs = study.to_crs("EPSG:4326")
	OUT_BOUNDARY.parent.mkdir(exist_ok=True)
	gpd.GeoDataFrame({"name": ["gba_plus_10km"], "area_km2": [round(area, 1)]},
	                 geometry=study_wgs, crs="EPSG:4326").to_file(OUT_BOUNDARY, driver="GeoJSON")

	cells = sorted(h3.geo_to_cells(study_wgs.iloc[0], H3_RES))
	if not EXPECTED_HEXES[0] <= len(cells) <= EXPECTED_HEXES[1]:
		raise SystemExit(f"{len(cells):,} hexes, expected {EXPECTED_HEXES} — check the CRS round-trip or H3_RES.")

	hexes = gpd.GeoDataFrame(
		{"h3": cells},
		geometry=[Polygon([(lng, lat) for lat, lng in h3.cell_to_boundary(c)]) for c in cells],
		crs="EPSG:4326",
	)
	centres = [h3.cell_to_latlng(c) for c in cells]
	lats = [p[0] for p in centres]
	lngs = [p[1] for p in centres]
	if not (12.5 < min(lats) and max(lats) < 13.5 and 77.0 < min(lngs) and max(lngs) < 78.2):
		raise SystemExit(f"hex centres span lat {min(lats):.2f}..{max(lats):.2f}, "
		                 f"lng {min(lngs):.2f}..{max(lngs):.2f} — coordinates look swapped.")
	hexes.to_file(OUT_HEXES, driver="GeoJSON")

	hex_area = hexes.to_crs(METRIC).area
	print(f"H3 res {H3_RES}     {len(cells):,} hexes   {hex_area.mean() / 1e6:.3f} km2 mean   "
	      f"covering {hex_area.sum() / 1e6:,.0f} km2")
	print(f"              centres lat {min(lats):.3f}..{max(lats):.3f}, lng {min(lngs):.3f}..{max(lngs):.3f}")
	print(f"\nwrote {OUT_BOUNDARY}\nwrote {OUT_HEXES}")
	print(f"\n{len(cells):,} hexes x 8 years = {len(cells) * 8:,} rows for the M2 table")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
