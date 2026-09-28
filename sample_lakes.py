"""Milestone 4, step 0: what a 1-5 ha OSM "lake" actually is, on a random sample.

Before any size cutoff is chosen, look at what sits just above it. Fifteen lakes
are drawn at random (fixed seed, drawn before looking) from one size band of
`results/m4_ring_pixels.csv` (`--band LO HI` in hectares, 1-5 by default), and
each gets:

  * its OSM tags and last editor, from the OSM API (Overpass was down 2026-09-28)
  * what Nominatim says is at its centre
  * the share of its pixels that read as water (MNDWI > 0, counted per pixel)
    in every dry season 2019-2026 and in the 2025 post-monsoon (Oct-Dec), so a
    tank that only fills in the rains is told apart from one that never holds
    water, and from a pool that always does
  * a high-resolution photo (Esri World Imagery) and Sentinel-2 true colour for
    2019 and 2026, outline drawn

Writes `results/m4_lake_sample/<LO>-<HI>ha/`: `sample.csv` and `index.html` beside
the frames.
The Esri frames are for looking at, not for publishing.
"""

import json
import os
import socket
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import ee
import geopandas as gpd
import pandas as pd
from PIL import Image, ImageDraw

from measure_rings import BOUNDARY, METRIC, WATER, lakes

SEED = 20260928
N = 15
BAND_HA = tuple(float(v) for v in sys.argv[sys.argv.index("--band") + 1 :][:2]) if "--band" in sys.argv else (1.0, 5.0)
YEARS = list(range(2019, 2027))
MONSOON = ("2025-10-01", "2025-12-31")
FRAME_PAD_M = 80
FRAME_PX = 420
RGB_MAX = 3000
NET_TIMEOUT_S = 180
UA = "bangalore-blue-green/0.1 (personal research)"

RINGS = Path("results/m4_ring_pixels.csv")
OUT = Path("results/m4_lake_sample") / f"{BAND_HA[0]:g}-{BAND_HA[1]:g}ha"
ESRI = "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"


def get_json(url: str) -> dict:
	with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as fh:
		return json.load(fh)


def osm_tags(keys: list[str]) -> dict[str, dict]:
	found = {}
	for kind, prefix in (("ways", "w"), ("relations", "r")):
		ids = [k[1:] for k in keys if k[0] == prefix]
		if ids:
			data = get_json(f"https://api.openstreetmap.org/api/0.6/{kind}.json?{kind}={','.join(ids)}")
			found |= {f"{prefix}{e['id']}": e for e in data["elements"]}
	return found


def place(lat: float, lon: float) -> str:
	time.sleep(1.1)
	query = urllib.parse.urlencode({"lat": lat, "lon": lon, "zoom": 17, "format": "json"})
	return get_json(f"https://nominatim.openstreetmap.org/reverse?{query}").get("display_name", "")


def water_share(fc: ee.FeatureCollection, start: str, end: str) -> dict[str, dict]:
	composite = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(fc).filterDate(start, end).median()
	image = (
		composite.normalizedDifference(["B3", "B11"]).gt(0).rename("water")
		.addBands(composite.normalizedDifference(["B8", "B4"]).rename("green"))
	)
	stats = image.reduceRegions(collection=fc, reducer=ee.Reducer.mean(), crs=METRIC, scale=10)
	return {f["properties"]["key"]: f["properties"] for f in stats.getInfo()["features"]}


def esri_frame(box, lake, path: Path) -> None:
	w, s, e, n = box
	query = urllib.parse.urlencode({
		"bbox": f"{w},{s},{e},{n}", "bboxSR": 4326, "imageSR": 4326,
		"size": f"{FRAME_PX},{FRAME_PX}", "format": "jpg", "f": "image",
	})
	urllib.request.urlretrieve(f"{ESRI}?{query}", path)
	image = Image.open(path).convert("RGB")
	draw = ImageDraw.Draw(image)
	for ring in getattr(lake, "geoms", [lake]):
		pts = [((x - w) / (e - w) * FRAME_PX, (n - y) / (n - s) * FRAME_PX) for x, y in ring.exterior.coords]
		draw.line(pts, fill=(255, 230, 0), width=2)
	image.save(path, quality=88)


def s2_frame(year: int, box, outline: ee.FeatureCollection, path: Path) -> None:
	region = ee.Geometry.Rectangle(list(box))
	composite = (
		ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(region)
		.filterDate(f"{year}-02-01", f"{year}-03-31").median()
	)
	edge = ee.Image().byte().paint(outline, 1, 1).selfMask().visualize(palette=["#ffe600"])
	image = composite.visualize(bands=["B4", "B3", "B2"], min=0, max=RGB_MAX).blend(edge)
	url = image.getThumbURL({"region": region, "dimensions": FRAME_PX // 2, "format": "jpg"})
	urllib.request.urlretrieve(url, path)


def page(table: pd.DataFrame) -> str:
	cards = []
	for r in table.itertuples():
		dry = " ".join(f"{int(getattr(r, f'water_{y}') * 100)}" for y in YEARS)
		cards.append(f"""
<section><h2>{r.pick}. {r.name or "(unnamed)"} <small>{r.osm} · {r.ha:.2f} ha</small></h2>
<div class="frames"><img src="{r.key}_esri.jpg"><div><img src="{r.key}_2019.jpg"><img src="{r.key}_2026.jpg">
<p class="cap">Sentinel-2, Feb-Mar 2019 (top) and 2026</p></div></div>
<p><b>Water share, dry season 2019-2026 (%):</b> {dry} · <b>post-monsoon 2025:</b> {int(r.water_monsoon * 100)}%
· <b>greenness 2026:</b> {r.green_2026:.2f}</p>
<p><b>OSM:</b> <code>{r.tags}</code> · edited {r.edited} by {r.editor}</p>
<p><b>Nominatim:</b> {r.place}</p></section>""")
	return f"""<!doctype html><meta charset="utf-8"><title>M4 lake sample</title>
<style>body{{font:14px system-ui;max-width:980px;margin:24px auto;padding:0 16px}}
.frames{{display:flex;gap:8px}} .frames>div{{display:flex;flex-direction:column;gap:8px}}
img{{display:block}} small{{color:#666;font-weight:normal}} .cap{{margin:0;color:#666;font-size:12px}}
section{{border-top:1px solid #ddd;padding-top:8px;margin-top:16px}} code{{font-size:12px}}</style>
<h1>What a {BAND_HA[0]:g}-{BAND_HA[1]:g} ha OSM lake is — {len(table)} drawn at random (seed {SEED})</h1>{"".join(cards)}"""


def main() -> int:
	project = os.environ.get("EE_PROJECT")
	if not project:
		sys.exit("Set EE_PROJECT to your Google Cloud project id first.")
	socket.setdefaulttimeout(NET_TIMEOUT_S)
	ee.Initialize(project=project)

	rings = pd.read_csv(RINGS)
	pick = rings[rings.ha.between(*BAND_HA, inclusive="left")].sample(N, random_state=SEED)
	boundary = gpd.read_file(BOUNDARY).to_crs(METRIC).union_all()
	shapes = lakes(gpd.read_file(WATER).to_crs(METRIC).assign(
		geometry=lambda f: f.geometry.make_valid()), boundary).set_index("osm")
	frame = gpd.GeoDataFrame(pick.set_index("osm"), geometry=shapes.geometry.reindex(pick.osm).values, crs=METRIC)
	frame = frame.reset_index().assign(pick=range(1, N + 1), key=lambda f: f.osm.str.replace(";", "_"))
	wgs = frame.to_crs("EPSG:4326")

	fc = ee.FeatureCollection([ee.Feature(ee.Geometry(g.__geo_interface__), {"key": k})
		for g, k in zip(wgs.geometry, wgs.key)])
	dry = {y: water_share(fc, f"{y}-02-01", f"{y}-03-31") for y in YEARS}
	monsoon = water_share(fc, *MONSOON)
	tags = osm_tags([k for keys in frame.osm for k in keys.split(";")])

	OUT.mkdir(parents=True, exist_ok=True)
	rows = []
	for r, g in zip(frame.itertuples(), wgs.geometry):
		box = gpd.GeoSeries([r.geometry.buffer(FRAME_PAD_M).envelope], crs=METRIC).to_crs("EPSG:4326").total_bounds
		esri_frame(box, g, OUT / f"{r.key}_esri.jpg")
		one = ee.FeatureCollection([ee.Feature(ee.Geometry(g.__geo_interface__))])
		for year in (2019, 2026):
			s2_frame(year, box, one, OUT / f"{r.key}_{year}.jpg")
		first = tags[r.osm.split(";")[0]]
		centre = g.representative_point()
		rows.append({
			"pick": r.pick, "osm": r.osm, "key": r.key, "name": "" if pd.isna(r.name) else r.name, "ha": r.ha,
			**{f"water_{y}": round(dry[y][r.key].get("water") or 0, 3) for y in YEARS},
			"water_monsoon": round(monsoon[r.key].get("water") or 0, 3),
			"green_2026": round(dry[2026][r.key].get("green") or 0, 3),
			"tags": ";".join(f"{k}={v}" for k, v in first.get("tags", {}).items() if k != "created_by"),
			"edited": first.get("timestamp", "")[:10], "editor": first.get("user", ""),
			"place": place(centre.y, centre.x), "lat": round(centre.y, 5), "lon": round(centre.x, 5),
		})
		print(f"{r.pick:>2} {r.osm:<14} {r.ha:5.2f} ha  done")

	table = pd.DataFrame(rows)
	table.drop(columns="key").to_csv(OUT / "sample.csv", index=False)
	(OUT / "index.html").write_text(page(table))
	print(f"wrote {OUT}/index.html and sample.csv")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
