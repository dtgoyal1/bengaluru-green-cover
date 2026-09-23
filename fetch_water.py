"""Fetch every mapped water body in the study area from OSM and cache it as GeoJSON.

Rule C (the water exclusion) looks at the imagery: a hex is water if it reads wet
on average. A lake under weed or marsh never reads wet, so a hex that is half lake
can pass it — `m2_hex_deep_dive.ipynb` found exactly that at Bellandur. This file
is the independent view: where OSM says water is *meant* to be, whatever it looked
like from orbit. Section 10 of `m2_hex_table.ipynb` reads it.

Classes kept, by the first tag that matches:
  wastewater  water=wastewater (treatment-plant ponds)
  wetland     natural=wetland
  water       natural=water (lakes, ponds, tanks; rivers and drains are dropped
              as thin lines that add almost no area)
  reservoir   landuse=reservoir or basin

One Overpass query for the whole boundary box. Multipolygon relations are built
from their outer and inner rings; any relation Overpass returns without member
geometry falls back to a Nominatim lookup, which returns it pre-assembled.
"""

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import geopandas as gpd
from shapely.geometry import LineString, MultiPolygon, Polygon, mapping, shape
from shapely.ops import polygonize, unary_union
from shapely.validation import make_valid

UA = "bangalore-blue-green/0.1 (personal research)"
BOUNDARY = Path("data/study_boundary.geojson")
OUT = Path("data/osm_water.geojson")
MIRRORS = ("https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter")
THIN = {"river", "stream", "canal", "drain", "ditch"}


def overpass(query: str) -> dict:
	for attempt in range(6):
		url = MIRRORS[attempt % len(MIRRORS)]
		try:
			req = urllib.request.Request(url, data=urllib.parse.urlencode({"data": query}).encode(),
				headers={"User-Agent": UA})
			with urllib.request.urlopen(req, timeout=400) as fh:
				return json.load(fh)
		except Exception as exc:
			print(f"  {url.split('/')[2]} attempt {attempt + 1} failed: {exc}")
			time.sleep(20)
	raise RuntimeError("overpass unavailable")


def nominatim(ids: list[int]) -> dict[int, dict]:
	found = {}
	for i in range(0, len(ids), 50):
		url = "https://nominatim.openstreetmap.org/lookup?" + urllib.parse.urlencode(
			{"osm_ids": ",".join(f"R{r}" for r in ids[i : i + 50]), "format": "json", "polygon_geojson": 1}
		)
		with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as fh:
			found |= {int(r["osm_id"]): r["geojson"] for r in json.load(fh)}
		time.sleep(1.1)
	return found


def classify(tags: dict) -> str | None:
	if tags.get("water") == "wastewater":
		return "wastewater"
	if tags.get("natural") == "wetland":
		return "wetland"
	if tags.get("natural") == "water":
		return None if tags.get("water") in THIN else "water"
	if tags.get("landuse") in ("reservoir", "basin"):
		return "reservoir"
	return None


def rings(members: list[dict], role: str):
	lines = [LineString([(p["lon"], p["lat"]) for p in m["geometry"]])
		for m in members if m.get("role") == role and len(m.get("geometry", [])) >= 2]
	return unary_union(list(polygonize(unary_union(lines)))) if lines else None


def polygonal(geom):
	if geom is None:
		return None
	geom = make_valid(geom)
	if isinstance(geom, (Polygon, MultiPolygon)):
		return geom
	parts = [g for g in getattr(geom, "geoms", []) if isinstance(g, (Polygon, MultiPolygon))]
	return unary_union(parts) if parts else None


def build(el: dict):
	if el["type"] == "way":
		pts = [(p["lon"], p["lat"]) for p in el.get("geometry", [])]
		return polygonal(Polygon(pts)) if len(pts) >= 4 and pts[0] == pts[-1] else None
	outer = rings(el.get("members", []), "outer")
	if outer is None:
		return None
	inner = rings(el.get("members", []), "inner")
	return polygonal(outer.difference(inner) if inner is not None else outer)


def main() -> int:
	w, s, e, n = gpd.read_file(BOUNDARY).total_bounds
	parts = "".join(f"{kind}{f};" for kind in ("way", "relation") for f in (
		"[natural=water]", "[natural=wetland]", '[landuse~"^(reservoir|basin)$"]'))
	started = time.time()
	data = overpass(f"[out:json][timeout:360][bbox:{s},{w},{n},{e}];({parts});out geom;")
	print(f"{len(data['elements']):,} elements in {time.time() - started:.0f}s")

	features, missing = [], []
	for el in data["elements"]:
		label = classify(el.get("tags", {}))
		if label is None:
			continue
		geom = build(el)
		if geom is None and el["type"] == "relation":
			missing.append(el)
			continue
		if geom is not None and not geom.is_empty:
			features.append((label, el, geom))

	if missing:
		print(f"{len(missing)} relations without member geometry — asking Nominatim")
		found = nominatim([el["id"] for el in missing])
		features += [(classify(el["tags"]), el, polygonal(shape(found[el["id"]])))
			for el in missing if el["id"] in found]
		print(f"  recovered {sum(el['id'] in found for el in missing)} of {len(missing)}")
	features = [(label, el, geom) for label, el, geom in features if geom is not None and not geom.is_empty]

	OUT.write_text(json.dumps({"type": "FeatureCollection", "features": [
		{
			"type": "Feature",
			"geometry": mapping(geom),
			"properties": {"class": label, "osm": f"{el['type'][0]}{el['id']}", "name": el.get("tags", {}).get("name", "")},
		}
		for label, el, geom in features
	]}))
	frame = gpd.read_file(OUT).to_crs("EPSG:32643")
	print(f"\nwrote {OUT} — {len(frame):,} polygons")
	print((frame.assign(km2=frame.area / 1e6).groupby("class").km2.agg(["count", "sum"]).round(2)).to_string())
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
