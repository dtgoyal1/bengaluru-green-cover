"""Milestone 0: authenticate against Earth Engine and print metadata for one
Sentinel-2 scene over Bangalore."""

import os
import sys

import ee

BANGALORE = (77.5946, 12.9716)


def main() -> int:
    project = os.environ.get("EE_PROJECT")
    if not project:
        sys.exit("Set EE_PROJECT to your Google Cloud project id first.")

    ee.Initialize(project=project)

    point = ee.Geometry.Point(BANGALORE)
    scene = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(point)
        .filterDate("2026-02-01", "2026-03-31")
        .sort("CLOUDY_PIXEL_PERCENTAGE")
        .first()
    )

    info = scene.getInfo()
    if info is None:
        sys.exit("No Sentinel-2 scene matched. Check the date window.")

    date = ee.Date(scene.get("system:time_start")).format("YYYY-MM-dd").getInfo()

    props = info["properties"]
    print(f"id            {info['id']}")
    print(f"date          {date}")
    print(f"cloud %       {props['CLOUDY_PIXEL_PERCENTAGE']:.2f}")
    print(f"tile          {props['MGRS_TILE']}")
    print(f"bands         {len(info['bands'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
