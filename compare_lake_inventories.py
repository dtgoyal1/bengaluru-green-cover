"""Milestone 4, step 0: how OSM's lakes compare with the official lake inventories.

A one-to-one join by name is hopeless (most OSM lakes and most KSRSAC tanks are
unnamed), so the comparison is by count and size, plus a spatial overlap rate:

  * size table: lakes per hectare band in each source, inside the study boundary
  * found in OSM: the share of each inventory's tanks that touch an OSM lake
    (polygons) or sit within 50 m of one (EMPRI points)
  * found in the inventory: the share of OSM lakes, per band, that touch a tank
  * area ratio: for matched pairs, OSM area over the inventory's area

EMPRI (the KLCDA revenue-record inventory, 2018) covers only BBMP + the BDA area,
so it is compared against OSM inside the convex hull of its own points, a stand-in
for that coverage. The polygon inventories are compared over the whole study
boundary. Inputs are the normalised files in `data/inventories/`.
"""

from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely

from measure_rings import BOUNDARY, METRIC, WATER, lakes

BINS = [0, 0.1, 1, 5, 10, 40, 100, float("inf")]
LABELS = ["<0.1", "0.1-1", "1-5", "5-10", "10-40", "40-100", "100+"]
POINT_MATCH_M = 50
INVENTORIES = Path("data/inventories")
POLYGON_SOURCES = {
	"KSRSAC tanks": ("ksrsac_tis_bu.geojson", "ksrsac_tis_br.geojson"),
	"ATREE lakes": ("atree_urban_rural.geojson",),
}
OUT = Path("results/m4_inventory_compare.csv")


def inside(frame: gpd.GeoDataFrame, area) -> gpd.GeoDataFrame:
	return frame[frame.representative_point().within(area)].reset_index(drop=True)


def banded(ha: pd.Series) -> pd.Series:
	return pd.cut(ha, BINS, labels=LABELS, right=False).value_counts().reindex(LABELS)


def main() -> int:
	boundary = gpd.read_file(BOUNDARY).to_crs(METRIC).union_all()
	osm = lakes(gpd.read_file(WATER).to_crs(METRIC).assign(geometry=lambda f: f.geometry.make_valid()), boundary)
	osm["ha"] = osm.area / 1e4

	rows = []
	for label, files in POLYGON_SOURCES.items():
		tanks = pd.concat([gpd.read_file(INVENTORIES / f).to_crs(METRIC) for f in files], ignore_index=True)
		tanks = inside(tanks.assign(geometry=tanks.geometry.make_valid()), boundary)
		tanks["ha"] = tanks.area / 1e4
		hits = gpd.sjoin(tanks[["ha", "geometry"]], osm[["ha", "geometry"]], predicate="intersects",
			lsuffix="inv", rsuffix="osm")
		pairs = hits.groupby(level=0).agg(inv=("ha_inv", "first"), osm=("ha_osm", "sum"))
		osm_hit = osm.index.isin(hits.index_osm)
		rows.append({
			"source": label, "area": "study boundary", "n": len(tanks), **banded(tanks.ha).to_dict(),
			"found_in_osm": round(tanks.index.isin(hits.index).mean(), 3),
			"osm_found_in_it_1ha+": round(osm_hit[osm.ha >= 1].mean(), 3),
			"osm_found_in_it_0.1-1": round(osm_hit[(osm.ha >= 0.1) & (osm.ha < 1)].mean(), 3),
			"osm_over_inv_area": round((pairs.osm / pairs.inv).median(), 2),
		})

	empri = pd.read_csv(INVENTORIES / "empri_bma_all.csv").dropna(subset=["lat", "lon"])
	empri = gpd.GeoDataFrame(empri, geometry=gpd.points_from_xy(empri.lon, empri.lat), crs="EPSG:4326").to_crs(METRIC)
	empri = empri[empri.within(boundary)].reset_index(drop=True)
	hull = shapely.convex_hull(empri.union_all())
	osm_bma = inside(osm, hull)
	near = gpd.sjoin_nearest(empri[["area_ha", "geometry"]], osm_bma[["ha", "geometry"]],
		max_distance=POINT_MATCH_M, how="inner")
	near = near[~near.index.duplicated()]
	osm_hit = osm_bma.index.isin(near.index_right)
	rows.append({
		"source": "EMPRI revenue inventory", "area": f"EMPRI hull ({hull.area / 1e6:,.0f} km2)", "n": len(empri),
		**banded(empri.area_ha).to_dict(),
		"found_in_osm": round(empri.index.isin(near.index).mean(), 3),
		"osm_found_in_it_1ha+": round(osm_hit[osm_bma.ha >= 1].mean(), 3),
		"osm_found_in_it_0.1-1": round(osm_hit[(osm_bma.ha >= 0.1) & (osm_bma.ha < 1)].mean(), 3),
		"osm_over_inv_area": round((near.ha / near.area_ha).median(), 2),
	})
	for area, frame in (("study boundary", osm), (f"EMPRI hull ({hull.area / 1e6:,.0f} km2)", osm_bma)):
		rows.append({"source": "OSM lakes", "area": area, "n": len(frame), **banded(frame.ha).to_dict()})

	table = pd.DataFrame(rows)
	table.to_csv(OUT, index=False)
	print(table.to_string(index=False))
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
