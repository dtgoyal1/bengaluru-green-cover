"""Milestone 5: the two swipe photos as plain map tiles, one folder per year.

Each year is ONE satellite pass, not the season median the numbers use: the
median takes in hazy late-March days and made 2019 look about 20% softer than
2026 (logged 2026-09-29). The whole study area is two Sentinel-2 tiles, 43PGQ and
43PHQ, on relative orbit 19, so a same-day mosaic covers it in one pass.

The days were chosen by the same test as the mockup: cloud-free over the whole
area, the same point in the season, and on three stable built-up patches (west,
east, south) no systematic brightness gap and similar sharpness:

  13 Feb 2019  (0.04% cloud)    6 Feb 2026  (0.05% cloud)

Tiles are fetched from Earth Engine's map tiles over the study boundary's box at
zoom 8-14 (z14 is about 9.3 m a pixel here, the native 10 m; gotcha 6 caps it
there), re-encoded as WebP and copied to `site/data/tiles/<year>/{z}/{x}/{y}.webp`.
Fetching is resumable: tiles already cached under `out/tiles/<year>/` are not
refetched. Plain tile files, not PMTiles: Cloudflare Pages ignores HTTP Range
requests, which PMTiles needs (logged 2026-10-05).
"""

import math
import os
import shutil
import socket
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path

import ee
import geopandas as gpd
from PIL import Image

DAYS = {2019: "20190213", 2026: "20260206"}
ZOOMS = range(8, 15)
RGB_MAX = 3000
WEBP_QUALITY = 78
WORKERS = 12
MAX_TRIES = 5
NET_TIMEOUT_S = 120

BOUNDARY = Path("data/study_boundary.geojson")
CACHE = Path("out/tiles")
OUT = Path("site/data/tiles")


def tile_range(bounds, z: int) -> tuple[range, range]:
	w, s, e, n = bounds
	scale = 2**z

	def tx(lon: float) -> int:
		return int((lon + 180) / 360 * scale)

	def ty(lat: float) -> int:
		r = math.radians(lat)
		return int((1 - math.asinh(math.tan(r)) / math.pi) / 2 * scale)

	return range(tx(w), tx(e) + 1), range(ty(n), ty(s) + 1)


def photo(day: str, region: ee.Geometry) -> ee.Image:
	return (
		ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
		.filterBounds(region)
		.filter(ee.Filter.stringStartsWith("system:index", day))
		.mosaic()
		.visualize(bands=["B4", "B3", "B2"], min=0, max=RGB_MAX)
	)


def fetch(fetcher, z: int, x: int, y: int, path: Path) -> None:
	if path.exists():
		return
	for attempt in range(MAX_TRIES):
		try:
			with urllib.request.urlopen(fetcher.format_tile_url(x, y, z), timeout=NET_TIMEOUT_S) as fh:
				image = Image.open(BytesIO(fh.read())).convert("RGB")
			path.parent.mkdir(parents=True, exist_ok=True)
			image.save(path, "WEBP", quality=WEBP_QUALITY, method=6)
			return
		except Exception as exc:
			if attempt == MAX_TRIES - 1:
				raise RuntimeError(f"tile {z}/{x}/{y} failed") from exc
			time.sleep(5 * (attempt + 1))


def publish(year: int, tiles: list[tuple[int, int, int]]) -> Path:
	path = OUT / str(year)
	shutil.rmtree(path, ignore_errors=True)
	for z, x, y in tiles:
		dest = path / f"{z}/{x}/{y}.webp"
		dest.parent.mkdir(parents=True, exist_ok=True)
		shutil.copyfile(CACHE / str(year) / f"{z}/{x}/{y}.webp", dest)
	return path


def main() -> int:
	project = os.environ.get("EE_PROJECT")
	if not project:
		sys.exit("Set EE_PROJECT to your Google Cloud project id first.")
	socket.setdefaulttimeout(NET_TIMEOUT_S)
	ee.Initialize(project=project)

	bounds = gpd.read_file(BOUNDARY).to_crs("EPSG:4326").total_bounds
	w, s, e, n = bounds
	region = ee.Geometry.Rectangle([w, s, e, n])
	for year, day in DAYS.items():
		fetcher = photo(day, region).getMapId()["tile_fetcher"]
		tiles = [(z, x, y) for z in ZOOMS for xs, ys in [tile_range(bounds, z)] for x in xs for y in ys]
		started = time.time()
		with ThreadPoolExecutor(WORKERS) as pool:
			list(pool.map(lambda t: fetch(fetcher, *t, CACHE / str(year) / f"{t[0]}/{t[1]}/{t[2]}.webp"), tiles))
		path = publish(year, tiles)
		size = sum(f.stat().st_size for f in path.rglob("*.webp"))
		print(f"{year} ({day}): {len(tiles)} tiles in {time.time() - started:.0f}s -> {path} ({size / 1e6:.1f} MB)")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
