"""Fetch the milestone 1 site polygons from OSM and cache them as GeoJSON.

Sites are pinned by OSM id, not by name search: hand-entered coordinates are
untrustworthy (gotcha 7) and a name search returns the wrong object with
depressing ease — "Lalbagh Botanical Garden" resolves to a different garden 20km
away, and a bare "Lalbagh" resolves to a railway station. Each id is still
checked against the bounding box it must fall inside.
"""

import json
import urllib.parse
import urllib.request
from pathlib import Path

UA = "bangalore-blue-green/0.1 (personal research)"
OUT = Path("data/osm_sites.geojson")

# name -> (osm id, must fall within (min_lat, min_lon, max_lat, max_lon))
SITES = {
	"lalbagh": ("W15802464", (12.93, 77.57, 12.97, 77.60)),
	"kaikondrahalli_lake": ("R6820030", (12.90, 77.66, 12.93, 77.68)),
	"varthur_lake": ("R19306126", (12.93, 77.71, 12.96, 77.75)),
	"varthur_area": ("R19883430", (12.91, 77.70, 12.97, 77.78)),
}


def lookup(osm_ids: list[str]) -> list[dict]:
	url = "https://nominatim.openstreetmap.org/lookup?" + urllib.parse.urlencode(
		{"osm_ids": ",".join(osm_ids), "format": "json", "polygon_geojson": 1}
	)
	req = urllib.request.Request(url, headers={"User-Agent": UA})
	with urllib.request.urlopen(req, timeout=60) as fh:
		return json.load(fh)


def main() -> int:
	by_id = {f"{r['osm_type'][0].upper()}{r['osm_id']}": r for r in lookup([i for i, _ in SITES.values()])}

	features = []
	for name, (osm_id, box) in SITES.items():
		hit = by_id.get(osm_id)
		if hit is None:
			print(f"{name:<22} NOT FOUND — {osm_id} returned nothing")
			continue
		min_lat, min_lon, max_lat, max_lon = box
		lat, lon = float(hit["lat"]), float(hit["lon"])
		if not (min_lat <= lat <= max_lat and min_lon <= lon <= max_lon):
			print(f"{name:<22} REJECTED — {osm_id} centres at {lat},{lon}, outside {box}")
			continue
		features.append({
			"type": "Feature",
			"geometry": hit["geojson"],
			"properties": {"site": name, "osm": osm_id, "display_name": hit["display_name"]},
		})
		print(f"{name:<22} {hit['geojson']['type']:<12} {osm_id:<11} {hit['display_name'][:50]}")

	OUT.parent.mkdir(exist_ok=True)
	OUT.write_text(json.dumps({"type": "FeatureCollection", "features": features}, indent=1))
	print(f"\nwrote {OUT} ({len(features)}/{len(SITES)} sites)")
	return 0 if len(features) == len(SITES) else 1


if __name__ == "__main__":
	raise SystemExit(main())
