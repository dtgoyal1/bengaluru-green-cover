# Bangalore Blue-Green Change (2016–2026)

**One-liner:** A static, interactive scrollytelling site showing exactly where Bangalore's tree canopy and water bodies gained or lost ground over ten years, using free Sentinel-2 imagery — measured per pixel across a fixed city boundary, so the output is a map of *where* it changed rather than a city-wide average.

**Audience:** LinkedIn / general public. Target 5–10 minutes of engagement.
**Not building:** a live tool, a backend, a scraper, or anything that needs maintenance after launch.

---

## How to resume a session

Paste this file into a new chat and say which milestone you're on. Update the **Status** and **Decision log** sections at the end of every working session — that's the whole trick to making a slow project survive gaps.

---

## Status

**Current milestone:** 0 — setup
**Blocked on:** Nothing external. GEE registration is done. Needs the Cloud project id
pasted in — `ee.Initialize()` currently fails only with "no project found".
**Next action:** Run `EE_PROJECT=<id> .venv/bin/python check_setup.py`. Once that prints scene metadata,
milestone 0 is closed; milestone 1 (ground-truth spot check) is next — that also needs
3–5 locations chosen, which is a judgement call only Aditya can make.
**Last worked on:** 2026-09-06

Repo, venv (Python 3.13), `check_setup.py` and working OAuth credentials are in place.

---

## Scope decisions (settled — don't relitigate)

| Decision | Rationale |
|---|---|
| Satellite analysis first, property matrix later or never | Ten years of imagery is free and consistent; ten years of property prices doesn't exist in accessible form |
| Everything precomputed, static hosting | No live tool needed. Zero maintenance, zero cost |
| Sentinel-2, 2016–2026 | One consistent sensor, 10m resolution, ~5-day revisit, covers exactly ten dry seasons |
| Dry-season (Feb–Mar) median composites, year-over-year | Anything shorter measures the monsoon, not development |
| Per-pixel analysis over a fixed boundary, aggregated to H3 hexes — not city-wide aggregates, not named-entity attribution | IISc's Energy & Wetlands group already owns the aggregate story; specificity is the differentiator. Pixel-level still answers *where*, which is what that rationale protects |
| H3 hex grid (~1km) as the reporting unit | Ward boundaries were redrawn in 2025 (198 → 369 wards across 5 corporations); historical joins are broken. Under the per-pixel pivot this is now the core spatial unit, not a supporting detail |
| Boundary: GBA outer boundary + ~10km ring | GBA alone (~712 km², 5 corporations, delimited 19.07.2025) excludes the peri-urban fringe where most change happened. The ring is a boundary we define, so state it explicitly when publishing. For pixel work the boundary is a clip mask, not a join key — any polygon is valid provided it is the same one for all ten years |
| Green (NDVI) first, blue (MNDWI) second and droppable | MNDWI is the same composite with different band math, so blue is nearly free once green works. If it proves noisy it can be cut without touching the pipeline |
| Show gains alongside losses | Restoration successes exist (Kaikondrahalli, Jakkur, Rachenahalli). Reads as analysis, not doom |

---

## Technical gotchas (learned before writing code — don't rediscover these)

1. **Seasonality dominates.** Bangalore greens up hard post-monsoon and browns by March. A March-vs-October comparison shows huge fake loss. Always compare the same window across years.
2. **Use MNDWI, not NDWI, for water.** NDWI produces false positives on rooftops and built-up surfaces. MNDWI (green vs SWIR) suppresses them.
3. **NDVI can't distinguish trees from grass or crops.** Peri-urban agriculture masquerades as canopy. Dry-season imagery helps (grass browns, trees hold). Consider Google Dynamic World for actual land-cover classes if this proves noisy.
4. **Compute area in a projected CRS, never in degrees.** EPSG:4326 is for storage and web display. For Bangalore, use EPSG:32643 (UTM 43N) for any area or distance math. Getting this wrong silently produces plausible-looking garbage.
5. **Cloud cover eats individual dates.** Median composites over a multi-week window handle this; single-date imagery will fail unpredictably.
6. **Raster volume will blow up static hosting.** Ship full tiles for only the two endpoint years; represent the middle eight as derived vector stats. Cap max zoom at z14.

---

## Stack

**Analysis:** Python — Earth Engine API (`earthengine-api`), `geopandas`, `shapely`, `h3`, `pandas`
**Export:** GeoJSON → PMTiles (via `tippecanoe`)
**Frontend:** MapLibre GL JS, Scrollama.js, Observable Plot. No framework needed.
**Hosting:** GitHub Pages or Cloudflare Pages

### Notes for a Java background

- **Earth Engine is declarative and runs server-side.** `ee.ImageCollection(...).filterDate(...).map(...).median()` builds a computation graph — nothing executes until you call `.getInfo()` or an export. It's Java Streams, except the terminal operation runs on Google's cluster. The failure mode is writing a Python `for` loop over image objects: it will appear to work, then be unusably slow or blow the request limit. Push everything into `.map()`.
- **Never pull rasters to the client.** `.getInfo()` on an image is a mistake. Reduce to numbers or vectors server-side, export those.
- **GeoJSON is just nested coordinate arrays** — `[lon, lat]`, in that order, which is backwards from how everyone says it aloud. This is the single most common bug in geospatial code.
- **A GeoDataFrame is a pandas DataFrame with a `geometry` column** and an attached CRS. Spatial joins and overlays are DataFrame ops, not loops.
- Python's lack of types will hurt here more than usual because coordinate arrays all look alike. Consider adding type hints and running mypy — it's cheap insurance.

---

## Milestones

Each ends with something that runs standalone. Milestones 1–4 are the real project; 5–8 are presentation. Stalling after 4 still leaves a publishable written post.

**Scope changed 2026-09-06:** the unit of analysis is the pixel over a fixed boundary, not the named lake. See the decision log.

### 0 — Setup
- [x] GEE non-commercial registration approved
- [x] Repo created, Python env with the analysis deps (Python 3.13)
- [x] OAuth credentials working (`earthengine` + `cloud-platform` scopes)
- [ ] Cloud project id known, `ee.Initialize(project=...)` works locally
- **Done when:** a script authenticates and prints metadata for one Sentinel-2 scene over Bangalore

### 1 — Ground-truth spot check ⭐ most important
Pick 3–5 places whose recent history you personally know, and check the per-pixel
values behave. Aim for a spread of expected answers:
- somewhere unchanged (a mature park) → expect ~flat
- somewhere you watched get built over → expect clear loss
- somewhere restored → expect gain
- **Done when:** a small table of location × year NDVI you can eyeball against your own memory
- **Why it matters:** this is the only gate in the project that fails loudly and cheaply.
  Without it, "run NDVI over Bangalore and look at the map" has nothing in it that can
  visibly go wrong — a broken method produces a plausible map. Find that out here.

### 2 — City-wide green
Dry-season (Feb–Mar) median composite per year, 2016–2026, clipped to the boundary.
Per-pixel NDVI, then aggregate to H3 hexes.
- **Done when:** a hex-level NDVI time series covering the whole boundary, and a
  2016 vs 2026 per-pixel change layer
- **Watch:** gotcha 3 escalates here. At pixel level across the fringe, peri-urban
  agriculture is a large share of the frame and greens/browns seasonally. Dynamic World
  moves from "consider if noisy" to "probably needed."

### 3 — Blue layer (optional)
MNDWI over the same composites. Same pipeline, different band math.
- **Done when:** hex-level water time series, or a logged decision to drop it
- Pre-approved to cut if noisy.

### 4 — Buffer-zone cross-reference
Intersect detected loss pixels with legally protected lake and storm-water-drain buffers.
- **Done when:** a list of specific polygons where green/blue → built-up inside a protected buffer
- **Note:** Karnataka modified SWD buffers in 2025 and a KTCDA amendment was proposed for lake buffers. Verify current rules before publishing any claim here — this is the section most likely to be challenged.

### 5 — Static export
GeoJSON + PMTiles. Endpoint years as raster, middle years as vector stats.

### 6 — Frontend: swipe comparison
2016 vs 2026 draggable divider. Build this first — it's the centerpiece and everything else hangs off it.

### 7 — Scrollytelling + locality search
Scrollama beats: city-wide → the worst-hit hexes → buffer violations → a counter-example where green was gained. Then a search box so people can look up their own locality.

### 8 — Polish and post
Small-multiples grid of the biggest-change hexes as the preview image. Record a 20s screen capture of the swipe; post it natively (LinkedIn suppresses posts with outbound links) and put the URL in the first comment.

---

## Data sources

| Source | What for | Notes |
|---|---|---|
| Sentinel-2 (via GEE) | The whole analysis | 10m, ~5-day revisit, 2015/16 onward |
| Landsat (via GEE) | Optional longer baseline | 30m, back to the 1980s |
| Google Dynamic World | Land-cover classes if NDVI is too noisy | 10m, near-real-time |
| OpenCity (`data.opencity.in`) | Lake inventory, ATREE lakes & streams map, zone-wise tree census (Nov 2024, Jan/Apr 2025), GBA delimitation | Primary source for Bangalore civic data |
| OpenStreetMap / Overpass | Amenity and boundary data | Mainly relevant if the property matrix happens |

---

## Decision log

Append one line per session. Date, what changed, why.

- 2026-09-06 — Project scoped. Satellite analysis chosen over property matrix as the first build.
- 2026-09-06 — Repo created. Python pinned to 3.13, not 3.14: geospatial wheels (shapely/pyproj/pyogrio) have no cp314 builds yet and would compile from source. `h3` resolves to 4.5.0, i.e. the v4 API (`latlng_to_cell`), not v3's `geo_to_h3` — relevant at milestone 3. Deps pinned exactly, since this project expects long gaps between sessions.
- 2026-09-06 — `earthengine authenticate` (default mode) was blocked by Google with "This app is blocked". It delegates to `gcloud auth application-default login` using Google's shared gcloud client ID and requests the `drive` scope, which the CLI itself warns is being restricted for that client. Re-running as `--auth_mode=localhost --scopes=earthengine,cloud-platform` succeeded. Two variables changed at once (EE's own client ID `517222506229-…` instead of gcloud's, and dropped `drive`+`devstorage`), so the block is NOT cleanly attributed to either — don't cite one as the cause.
- 2026-09-06 — Consequence of those reduced scopes: no `Export.table.toDrive` and no GCS export. Under the per-pixel pivot this bites LATER than first logged, not sooner: hex stats reduce server-side to a few thousand rows × 10 years, which returns fine as CSV/vector on the current scopes. Raster export is only needed for the M5/M6 endpoint-year tiles; the documented fix then is registering an own OAuth client ID rather than re-adding `drive` to the shared one.
- 2026-09-06 — `.gitignore` excludes `data/`, `out/`, `*.geojson` and rasters to keep static-hosting bloat out of git (gotcha 6). Milestone 1's five-lake CSV and milestone 5's GeoJSON exports are deliverables that *should* be committed — put those in a tracked `results/` dir or add a negation pattern when the time comes.

---
- 2026-09-06 — **Scope change: per-pixel, not per-lake.** The unit of analysis is now the pixel over a fixed boundary, aggregated to H3 hexes; named lakes are out. M1 (five-lake validation) became a ground-truth spot check on 3–5 personally-known locations — the unit changed, the gate did not, because it is the only cheap way for a broken method to fail loudly. M2 (all lakes) dissolved into the city-wide run. M3 (canopy) became the core and moved up. M4 (buffers) survives and fits better, since loss *pixels* intersect buffer polygons more naturally than lake polygons did.
- 2026-09-06 — Boundary chosen: GBA outer boundary + ~10km ring. GBA alone (~712 km²) stops short of Whitefield/Sarjapur/North Bangalore, where most of the change is. The ring is self-defined, so it must be stated explicitly when publishing.
- 2026-09-06 — Green (NDVI) is the priority; blue (MNDWI) is pre-approved to drop if noisy. Gotcha 3 (NDVI can't separate trees from grass/crops) escalates under the pixel pivot — peri-urban agriculture is a large share of the fringe, so Dynamic World is now likely rather than optional.

## Parked: the property/quality matrix

Not dead, just later. If revived, the key insights already worked out:

- The scatter plot will show a strong diagonal because price already reflects quality. **The residual is the finding**, not the plot: which localities are cheaper or dearer than their infrastructure justifies.
- Price prices the future; quality measures the present. Carry *change in quality over 5 years* as a third dimension, or metro-adjacent areas will look overpriced when they're just early.
- 6–8 metrics maximum. Check the correlation matrix first — if everything loads onto distance-from-centre, you've built an expensive centrality index.
- Prioritise metrics that vary independently of centrality: Cauvery connection vs. borewell, flooding history, commute time to *employment clusters* (Whitefield/ORR/E-City, not the geographic centre), canopy, air quality.
- Make the weights user-adjustable sliders. The weighting is inherently contestable; sliders turn that into a feature.
- Consider rent over sale price — rent tracks current livability, sale price embeds speculation. The rent-to-price ratio is itself a signal.
- **Milestone 3's canopy output feeds directly into this**, and it's the input nobody else has at this granularity.
