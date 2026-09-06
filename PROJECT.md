# Bangalore Blue-Green Change (2016–2026)

**One-liner:** A static, interactive scrollytelling site showing exactly where Bangalore's tree canopy and water bodies gained or lost ground over ten years, using free Sentinel-2 imagery — with per-lake and per-parcel attribution rather than city-wide averages.

**Audience:** LinkedIn / general public. Target 5–10 minutes of engagement.
**Not building:** a live tool, a backend, a scraper, or anything that needs maintenance after launch.

---

## How to resume a session

Paste this file into a new chat and say which milestone you're on. Update the **Status** and **Decision log** sections at the end of every working session — that's the whole trick to making a slow project survive gaps.

---

## Status

**Current milestone:** 0 — setup
**Blocked on:** A Google Cloud project id. OAuth is done and the token refreshes;
`ee.Initialize()` now fails only with "no project found".
**Next action:** Register the account at <https://code.earthengine.google.com/register>
(non-commercial), which creates or attaches a Cloud project. Then
`EE_PROJECT=<id> .venv/bin/python check_setup.py`. Once that prints scene metadata,
milestone 0 is closed; milestone 1 (five-lake validation) is next.
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
| Per-lake and per-hex attribution, not city-wide aggregates | IISc's Energy & Wetlands group already owns the aggregate story; specificity is the differentiator |
| H3 hex grid (~1km) as the spatial unit | Ward boundaries were redrawn in 2025 (198 → 369 wards across 5 corporations); historical joins are broken |
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

### 0 — Setup
- [ ] GEE non-commercial registration approved (has 1–2 day lead time)
- [ ] Google Cloud project created, `ee.Initialize()` works locally
- [ ] Repo created, Python env with the analysis deps
- **Done when:** a script authenticates and prints metadata for one Sentinel-2 scene over Bangalore

### 1 — Five-lake validation ⭐ most important
Compute annual dry-season surface area, 2016–2026, for: Bellandur, Varthur, Kaikondrahalli, Jakkur, and one you know personally.
- **Done when:** a CSV of 5 lakes × 10 years that you can eyeball against reality
- **Why it matters:** if the method says Kaikondrahalli shrank, the method is broken. Find that out now, not after building a frontend on top of it.

### 2 — Scale to all lakes
Same pipeline across the full lake inventory. Produce ranked biggest-losers and biggest-recoveries lists.
- **Done when:** a CSV of every lake × 10 years, plus the two ranked lists

### 3 — Canopy layer
Dry-season NDVI per H3 hex, ten years.
- **Done when:** hex-level canopy time series covering the GBA area

### 4 — Buffer-zone cross-reference
Intersect detected loss with legally protected lake and storm-water-drain buffers.
- **Done when:** a list of specific polygons where green/blue → built-up inside a protected buffer
- **Note:** Karnataka modified SWD buffers in 2025 and a KTCDA amendment was proposed for lake buffers. Verify current rules before publishing any claim here — this is the section most likely to be challenged.

### 5 — Static export
GeoJSON + PMTiles. Endpoint years as raster, middle years as vector stats.

### 6 — Frontend: swipe comparison
2016 vs 2026 draggable divider. Build this first — it's the centerpiece and everything else hangs off it.

### 7 — Scrollytelling + locality search
Scrollama beats: city-wide → one dramatic lake → buffer violations → a counter-example. Then a search box so people can look up their own locality.

### 8 — Polish and post
Small-multiples grid of every lake as the preview image. Record a 20s screen capture of the swipe; post it natively (LinkedIn suppresses posts with outbound links) and put the URL in the first comment.

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
- 2026-09-06 — Consequence of those reduced scopes: no `Export.table.toDrive` and no GCS export. Fine through milestone 1 (5 lakes × 10 years is ~50 numbers via `getInfo()`). Expect this to bite at milestone 2 (all lakes); the documented fix is registering an own OAuth client ID rather than re-adding `drive` to the shared one.
- 2026-09-06 — `.gitignore` excludes `data/`, `out/`, `*.geojson` and rasters to keep static-hosting bloat out of git (gotcha 6). Milestone 1's five-lake CSV and milestone 5's GeoJSON exports are deliverables that *should* be committed — put those in a tracked `results/` dir or add a negation pattern when the time comes.

---

## Parked: the property/quality matrix

Not dead, just later. If revived, the key insights already worked out:

- The scatter plot will show a strong diagonal because price already reflects quality. **The residual is the finding**, not the plot: which localities are cheaper or dearer than their infrastructure justifies.
- Price prices the future; quality measures the present. Carry *change in quality over 5 years* as a third dimension, or metro-adjacent areas will look overpriced when they're just early.
- 6–8 metrics maximum. Check the correlation matrix first — if everything loads onto distance-from-centre, you've built an expensive centrality index.
- Prioritise metrics that vary independently of centrality: Cauvery connection vs. borewell, flooding history, commute time to *employment clusters* (Whitefield/ORR/E-City, not the geographic centre), canopy, air quality.
- Make the weights user-adjustable sliders. The weighting is inherently contestable; sliders turn that into a feature.
- Consider rent over sale price — rent tracks current livability, sale price embeds speculation. The rent-to-price ratio is itself a signal.
- **Milestone 3's canopy output feeds directly into this**, and it's the input nobody else has at this granularity.
