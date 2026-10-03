# Bangalore Blue-Green Change (2019–2026)

**One-liner:** A static, interactive scrollytelling site showing exactly where Bangalore's tree canopy and water bodies gained or lost ground over ten years, using free Sentinel-2 imagery — measured per pixel across a fixed city boundary, so the output is a map of *where* it changed rather than a city-wide average.

**Audience:** LinkedIn / general public. Target 5–10 minutes of engagement.
**Not building:** a live tool, a backend, a scraper, or anything that needs maintenance after launch.

---

## How to resume a session

Paste this file into a new chat and say which milestone you're on. Update the **Status** and **Decision log** sections at the end of every working session — that's the whole trick to making a slow project survive gaps.

---

## Status

**Current milestone:** 6 — the site, built for real from `site/data/`. **M5 closed 2026-09-29.**
**M4 closed 2026-09-28** (provisionally, by Claude). **M3 dropped 2026-09-28.** **M2 closed 2026-09-27.**
**M1 closed 2026-09-11** on a 2-of-3 gate (flat ✓, loss ✓, gain ✗ — see below).
**Blocked on:** Nothing.
**Next action:** M6 for real: a static page in `site/` reading `site/data/` (MapLibre + the
PMTiles protocol), opening at city scale so the two fronts show — the north-west (Shivaram Karanth
Layout and its three lakes) and the east (Varthur to Hoskote). Scope confirmed by Aditya
2026-09-28/29: loss of green cover, and loss inside protected zones; lake works do not count; **no
gains anywhere on the site**.
**First-visitor review of the M6 build (2026-09-29):** `REVIEW-first-visitor-2026-09-29.md`.
Nothing acted on yet, and four open decisions for Aditya are at the bottom of it. Start the next
session there.

**M5's result, `site/data/`:** `2019.pmtiles` and `2026.pmtiles` (13 Feb 2019 and 6 Feb 2026, one
pass each, z8-14, WebP, 13.8 and 15.0 MB, gitignored — `export_tiles.py`), `hexes.geojson` (loss
only), `places.geojson` (22 places: 11 east, 5 north-west, 6 elsewhere; copy in `site/places.csv`),
`outlines.geojson`, `boundary.geojson`, `details.json` (the 38 checked losses for the method page) —
`export_vectors.py` — and `crops/` (44 card photos at native 10 m — `export_crops.py`).

**M6 spec (agreed 2026-09-29 on the mockup, https://claude.ai/artifact/L7fTNUpp9zhjyeSSMB6Av7):**
two pages. **Front page, visuals only:** headline, the full-width 2019 | 2026 photo swipe, one button
that shows the loss-only hexes (off at load), dots for *places* (neighbouring checked hexes merge
into one place, each lake is one place), a card per place (name, one plain sentence, Sentinel-2
before/after, a link to the method; no ranks, scores or verdict labels), a strip of places below
the map, locality search, a one-line footer. **"How it was made" page:** what was measured, the
city-average comparison, hexes and the lake mask, the photo check, lake buffers with a band diagram,
what this cannot see, the full table of every place (rank, 2020 re-rank, change, verdict, note),
sources. **Not shipped:** gains, lake works, doubtful places, a city-wide score, water, drains, the
per-pixel change map, readability and grid-check internals, Esri photos.

**M4's result:** `results/m4_ring_verdicts.csv` — the 40 biggest losses in the outer 20 m of the
30 m ring round the 590 OSM lakes of 1 ha or more, each photo-checked: **8 real loss**, 18 lake
works, 9 doubtful, 3 outline artefact, 1 water arrived, 1 weed swing (`m4_ring_photo_check.ipynb`).
The step 0 gate is `m4_ring_gate.ipynb`.

**M2's result:** `results/m2_loss_verdicts.csv` — every one of the 40 biggest losses photo-checked,
**30 quotable** (27 real loss, 3 real loss on wetland), 4 lake works and 6 doubtful left out of the
headline list (`m2_loss_photo_check.ipynb`). The per-pixel change map (`render_change_map.py`,
`m2_change_map.ipynb`) matches the table to 2e-5 on 100 hexes. **The lake-works call is confirmed** (Aditya,
2026-09-28): lake works are not loss, in M2 or M4.

**The ranking is end-minus-start** — normalised 2026 minus normalised 2019, losses and gains ranked
by size — decided 2026-09-23. The slope-vs-endpoint question is closed; the slope can still be
carried as a second column showing gradual vs sudden.

**The source table is now `results/m2_hex_table_masked.csv`** (`measure_hexes.py --mask-water`):
every pixel inside an OSM lake, pond, reservoir or sewage pond (`fetch_water.py` →
`data/osm_water.geojson`) is dropped before averaging, the same pixels every year. Wetlands are
**kept**. **Rule C is retired** — the masked table is read with no hex-level water exclusion;
`results/m2_water_hexes.csv` and `m2_hex_table.csv` stay committed as the before-state. Study
size: 2,868 hexes, 74.2 km² of pixels masked, no hex left with zero land.

Notebooks, in reading order (all but two re-run with no Earth Engine):
  - `m2_hex_table.ipynb` — the unmasked table: QC, normalisation (section 8), trend line vs
    end-minus-start (9), and the count that exposed the lake problem (10).
  - `m2_hex_deep_dive.ipynb` (EE) — three hexes up close: photos, raw vs normalised, per-pass
    spread, water share.
  - `m2_masked.ipynb` — what the mask changed: before/after top 40, where familiar hexes moved,
    what a 25% cutoff would do.
  - `m2_top_photo_check.ipynb` (EE) — photos of the masked top 12, water leaking past the mask, and
    Hesaraghatta against its OSM outline.
  - `m2_dynamic_world.ipynb` (EE) — can Dynamic World's labels be trusted: cleared soil, known
    places, noise floor, mode vs mean, WorldCover, and why it was dropped.
  - `m2_loss_photo_check.ipynb` (EE) — ranks 9-40 of the losses: water leak, photos, a verdict for
    all 40, and which verdicts depend on the 2019 start year.
  - `m2_change_map.ipynb` (EE) — the per-pixel map checked against the table, the whole study
    area with the 40 verdicts, and three places at 10 m.

**M2 is three layers, and only the third one downloads:**
  1. **Base** — greenness per pixel per year: 27M pixels x 8 years = 216M values. Stays server-side,
     never pulled (see the Java-background note on `.getInfo()`).
  2. **Change map** — the per-pixel difference, as a picture.
  3. **Hex table** — H3 res 8: **2,868 hexes x 8 years = 22,944 rows**. A small CSV. Rankings,
     locality search and charts are all built from this.

**Not in M2, and not in the project:** a city-wide aggregate score. Measured 2026-09-11 and it is
unreadable (t = 0.40, 95% range spans zero), and the scope table already cedes the aggregate story
to IISc. Do not reintroduce it.

Run `notebooks/m1_spot_check.ipynb` for the whole method end to end, and
`results/imagery/index.html` for the fastest eyeball check on any single number.
**Last worked on:** 2026-09-28

**`EE_PROJECT=project-id-0186438029819335325`** (display name "TAP", `roles/owner`,
`earthengine.googleapis.com` enabled). Not a credential, but it does travel with this file if the
repo goes public — move it to a gitignored file if that ever matters.

Repo, venv (Python 3.13), `check_setup.py` and working OAuth credentials are in place. M0 verified
2026-09-07: scene `COPERNICUS/S2_SR_HARMONIZED/20260201T050929_20260201T051504_T43PGQ`, tile 43PGQ,
0.00% cloud, 26 bands.

Two auth quirks worth not rediscovering. First, `ee.Initialize()` raising "no project found" is
**not** evidence a project exists and was merely unpassed — the client raises it identically when
none exists. Second, `gcloud projects list` returns `Listed 0 items` for this account even though
`gcloud projects describe <id>` succeeds and the account is owner, so a project can be perfectly
usable and invisible to `list`. Trust `describe`, or just run `check_setup.py`.

---

## Scope decisions (settled — don't relitigate)

| Decision | Rationale |
|---|---|
| Satellite analysis first, property matrix later or never | Ten years of imagery is free and consistent; ten years of property prices doesn't exist in accessible form |
| Everything precomputed, static hosting | No live tool needed. Zero maintenance, zero cost |
| Sentinel-2, 2019–2026 | One consistent sensor, 10m resolution, ~5-day revisit. **Eight dry seasons, not ten** — decided 2026-09-11. The corrected (L2A) product was backfilled patchily before 2019: Feb–Mar has 1 usable scene in 2016, 2–4 in 2017, 4–7 in 2018, then 12–28 from 2019 on. A median of two images cannot reject cloud, so the early years are a precision problem, not a coverage one. 2017–2018 stay in tables as thin context; 2016 is dropped |
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
3. **NDVI can't distinguish trees from grass or crops.** Peri-urban agriculture masquerades as canopy. Dry-season imagery helps (grass browns, trees hold). Consider Google Dynamic World for actual land-cover classes if this proves noisy. **Tried and dropped 2026-09-27** — it doesn't fix this (see the log); judge crop swings by eye.
4. **Compute area in a projected CRS, never in degrees.** EPSG:4326 is for storage and web display. For Bangalore, use EPSG:32643 (UTM 43N) for any area or distance math. Getting this wrong silently produces plausible-looking garbage.
5. **Cloud cover eats individual dates.** Median composites over a multi-week window handle this; single-date imagery will fail unpredictably.
6. **Raster volume will blow up static hosting.** Ship full tiles for only the two endpoint years; represent the middle eight as derived vector stats. Cap max zoom at z14.
7. **Never trust a recalled coordinate.** A point that misses its target by a few hundred metres still returns clean, plausible numbers — the Kaikondrahalli sample sat on land and produced a perfectly reasonable-looking NDVI series. Sanity-check every hand-entered location against something independent (MNDWI over a lake, a wider buffer, OSM) before reading meaning into its values.
8. **Interannual dry-season variability is large — difference against a control.** Distinct from gotcha 1, which is about comparing the wrong *months*. Even with the window fixed at Feb-Mar, whole years move together: in the M1 table Lalbagh, the Kaikondrahalli rim and Varthur all peak in 2021 and dip in 2024, on n=12-28 scenes, so it is not sampling noise but dry-season moisture and rainfall timing. The effect is comparable in size to eight years of real trend at one site, so an absolute per-year value cannot be read as change. Difference every site against a stable reference before claiming a trend.

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
- [x] GEE non-commercial eligibility approved, Cloud project linked
- [x] Repo created, Python env with the analysis deps (Python 3.13)
- [x] OAuth credentials working (`earthengine` + `cloud-platform` scopes)
- [x] Cloud project id known, `ee.Initialize(project=...)` works locally
- **Done when:** a script authenticates and prints metadata for one Sentinel-2 scene over Bangalore

### 1 — Ground-truth spot check ⭐ most important — **CLOSED 2026-09-11**

**Verdict: passed on 2 of 3 directions, closed deliberately on that basis.** flat ✓ (Lalbagh),
loss ✓ (Varthur, t = -3.18, and it survived a contamination check), gain ✗ (Kaikondrahalli rim, not
established at 50/100/200m). The gain direction was closed by decision, not by evidence: the
city-wide signal is invisible under rainfall noise, so a single modest restoration almost certainly
is too, and M2's own hex ranking will surface a larger one if it exists. Fix the selection rule
(top-N gaining hexes) *before* looking, or it is confirmation-shopping.

Pick 3–5 places whose recent history you personally know, and check the per-pixel
values behave. Aim for a spread of expected answers:
- somewhere unchanged (a mature park) → expect ~flat
- somewhere you watched get built over → expect clear loss
- somewhere restored → expect gain
- **Done when:** a small table of location × year NDVI you can eyeball against your own memory
- **Run 2026-09-07, re-run 2026-09-11:** `fetch_sites.py` then `spot_check.py` →
  `results/m1_spot_check.csv`. The rim is probed at three radii (`RIMS = (50, 100, 200)`) so a
  diluted gain would show as a gradient; the 200m rows reproduce the 09-07 baseline exactly.
- **Note:** `varthur_built` reports n=24-28 vs 12-14 elsewhere only because that polygon spans two
  MGRS tiles. It is scenes-intersecting, not scenes-per-pixel — coverage is equivalent, not better.
- **Why it matters:** this is the only gate in the project that fails loudly and cheaply.
  Without it, "run NDVI over Bangalore and look at the map" has nothing in it that can
  visibly go wrong — a broken method produces a plausible map. Find that out here.

### 2 — City-wide green — **CLOSED 2026-09-27**
- [x] **Step 0 — boundary + grid (2026-09-11).** `build_grid.py`. GBA outer boundary + 10km ring =
  2,174.9 km²; 2,868 H3 res-8 hexes (0.758 km² mean) covering 2,173 km².
- [x] **Step 1 — hex table (2026-09-11).** `measure_hexes.py` → `results/m2_hex_table.csv`.
  22,944 rows: h3, year, green, wet, n_pixels. Absolute values; relative change derived downstream.

Dry-season (Feb–Mar) median composite per year, 2019–2026, clipped to the boundary.
Per-pixel NDVI, then aggregate to H3 hexes.
- **Done when:** a hex-level NDVI time series covering the whole boundary, and a
  2019 vs 2026 per-pixel change layer
- **Watch:** water bodies are **not** masked — decided 2026-09-11, see the decision log. The mean is
  unaffected (0.92% of area, biasing *downward* by 0.002). The map is not: hyacinth reads as dense
  canopy and is invisible to MNDWI, so a cleared lake renders as canopy loss. Check the top-N
  changed hexes against imagery before any of them becomes a headline. If a per-year mask is ever
  reconsidered: it is disqualified, it makes things strictly worse.
  **Escalated 2026-09-16 — this is not a spot-check obligation, it is the dominant signal at the
  top of the ranking.** Of the 20 largest absolute 2019→2026 losses, 10 end wetter than −0.2
  against a city median of −0.454; the top 4 are all water arriving. Treat an unguarded top-N loss
  list as wrong by default, not as probably-fine-with-one-outlier. (The companion statistic logged
  that day — *18 of 20 got wetter over the run* — was **retired 2026-09-20**; it is an artefact of
  the −0.69 correlation between greenness change and wetness change, not evidence of water.)
  **Resolved 2026-09-20 — the eyeball is no longer the mitigation.** 50 water hexes (38 km², 1.7%)
  are excluded by rule C before any ranking exists; see the decision log and
  `results/m2_water_hexes.csv`. Eyeballing the survivors is now a backstop, not the defence.
  **Superseded 2026-09-23 — rule C leaked, replaced by a pixel mask.** Rule C still let 25 lake
  hexes into the top 40 (6.5× the city rate), because weed-covered, part-filled or seasonally dry
  lakes never read wet on a hex average. Mapped water is now masked per pixel before averaging
  (`measure_hexes.py --mask-water`), and rule C is no longer applied. See the 2026-09-23 log.
- [x] **Step 1b — masked hex table (2026-09-23).** `fetch_water.py`, then
  `measure_hexes.py --mask-water` → `results/m2_hex_table_masked.csv`. Same columns; `n_pixels` is
  the land left after masking.
- [x] **Step 2a — the ranking, photo-checked (2026-09-27).** End-minus-start on the masked table, 25%
  land cutoff, `check` flag (`m2_masked.ipynb` sections 6-7); all 40 biggest losses checked against
  imagery (`m2_top_photo_check.ipynb`, `m2_loss_photo_check.ipynb`) → `results/m2_loss_verdicts.csv`.
  30 quotable. The gains list was checked 2026-09-28 (`m2_gain_photo_check.ipynb`): 6 real gains.
- [x] **Step 2b — per-pixel change map (2026-09-27).** `render_change_map.py` →
  `results/m2_change_map.png` (gitignored, 18 m a pixel); `m2_change_map.ipynb` shows it matches the
  table (largest gap 2e-5 over 100 hexes).
- **Watch:** gotcha 8 forces the change layer to be *relative* — each hex against the city-wide
  median for that year, not against its own absolute value in 2019. An absolute per-hex delta will
  render a whole-city gain or loss that is only weather. Also gotcha 3 escalates here. At pixel level across the fringe, peri-urban
  agriculture is a large share of the frame and greens/browns seasonally. Dynamic World
  moves from "consider if noisy" to "probably needed." **Tested and dropped 2026-09-27** — see the log.

### 3 — Blue layer (optional) — **DROPPED 2026-09-28**
MNDWI over the same composites. **Not** the same pipeline, despite the band math being the only
difference at pixel level: measured 2026-09-16, a hex *mean* of MNDWI correlates −0.65 with
greenness and mostly reports "not vegetated", with only 5 of 2,868 hexes positive. The water test
has to be applied per pixel and the pixels then counted — threshold-then-count, not
average-then-threshold. `results/m2_hex_table.csv` already carries `wet` as a hex mean, so that
column is context, not the blue layer.
- **Done when:** hex-level water time series, or a logged decision to drop it
- Pre-approved to cut if noisy.

### 4 — Buffer-zone cross-reference — **CLOSED 2026-09-28**
Intersect vegetation loss with the RMP-2015 30 m lake buffer. **Lakes only, green only** (drains and
the blue layer dropped 2026-09-28): the 590 OSM lakes of 1 ha or more, the ring measured from
mapped water, the outer 20 m of it.
- **Done when:** a list of specific lakes where vegetation was lost within 30 m of mapped water,
  each photo-checked, with a verdict (reworded 2026-09-28 by Claude, provisional, from "polygons
  where green/blue → built-up inside a protected buffer")
- **Note:** Karnataka cut drain buffers in 2025, and the KTCDA lake-buffer amendment's status is
  contested between sources. The claim is about land protected when the period began. Verify
  current rules before publishing any claim here — this is the section most likely to be challenged.

### 5 — Static export — **CLOSED 2026-09-29**
GeoJSON + PMTiles. Endpoint years as raster, middle years as vector stats.

### 6 — Frontend: swipe comparison
2019 vs 2026 draggable divider. Build this first — it's the centerpiece and everything else hangs off it.
Spec agreed 2026-09-29 — see Status.

### 7 — Scrollytelling + locality search
Scrollama beats: city-wide → the worst-hit hexes → buffer violations. ~~A counter-example where green was gained~~ — dropped 2026-09-29 with gains. Then a search box so people can look up their own locality.

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
| KSRSAC storm-water drains (OpenCity, 2022 KML) | Classified drain centrelines, if drain buffers are ever reopened | BBMP only; public domain. Dropped from M4 2026-09-28 |
| Lake inventories (`data/inventories/`) | Cross-checking OSM lakes: KSRSAC Tank Information System, ATREE lakes, EMPRI 2018 revenue inventory | Fetched 2026-09-28; KSRSAC states no licence, ATREE is CC-BY |

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

- 2026-09-07 — EE is registered under the personal account `dt.goyal1@gmail.com`, not the osfin Workspace account that local `gcloud` defaults to (`osfin-gws-aditya-2026`). This **resolves** the commercial/non-commercial mismatch rather than leaving it open: a personal account is the correct owner for a non-commercial registration. `gcloud` now holds both accounts; the work one still needs interactive reauth.
- 2026-09-07 — M0's remaining blocker re-diagnosed: it is a missing *project*, not a missing *id*. `gcloud projects list` as the Gmail account returns zero projects. So the fix is the EE register page (which creates, enables and links in one pass), not `gcloud projects create` and not hunting for an id that was never issued.

- 2026-09-07 — **M0 closed.** `EE_PROJECT=project-id-0186438029819335325` works: `check_setup.py` returned live S2 metadata over Bangalore. Supersedes the two entries above — the project did exist and the account is owner on it; what misled the diagnosis was `gcloud projects list` returning zero items for a project the same account owns. `describe` and `check_setup.py` are the checks to trust, not `list`.

- 2026-09-07 — **`spot_check.py` written and run; M1 gate not yet passed.** Lalbagh (flat control) came back 0.529-0.593 NDVI across nine years with no trend — the pipeline behaves in the direction it was meant to. But flat and gain don't test loss, so the gate still hangs on one location only Aditya can supply.
- 2026-09-07 — **Scope problem: no usable 2016 dry season in the corrected product.** Corrected 2026-09-08 after checking properly — the earlier wording ("returns n=0") was wrong in a way worth not re-inheriting. The raw imagery for Feb-Mar 2016 exists in quantity: `S2_HARMONIZED` (L1C, top-of-atmosphere) has 12 scenes over Varthur. It is the atmospherically corrected `S2_SR_HARMONIZED` (L2A) we depend on that is thin, and it is thin by *patchy backfill*, not by a start date — full-year counts over Varthur run 2015 n=2, 2016 n=15, 2017 n=9, 2018 n=21, which isn't even monotonic. The Feb-Mar window specifically: 1 scene in 2016 (2016-02-19, 2.5% cloud), 2-4 in 2017, 4-7 in 2018, 12-14 from 2019. That lone 2016 scene is useless twice over — a single image cannot be medianed, so any haze in it passes straight through, and it sits on tile 43PHQ only, one of the two tiles Varthur straddles, so it doesn't even cover the site.
- 2026-09-07 — Why the early years can't just be topped up from L1C: haze biases top-of-atmosphere NDVI systematically low, so splicing L1C and L2A into one series manufactures a step change at the seam that is indistinguishable from real land-cover change. Untested idea, do not rely on it: control-differencing (gotcha 8) might partially cancel a shared atmospheric offset, since both site and control would carry it — but haze varies spatially, so cancellation would be partial at best and this has not been checked.
- 2026-09-07 — **NDVI is the wrong probe for a restored lake, and the first coordinate was wrong.** The Kaikondrahalli sample returned MNDWI about -0.30, i.e. no water in the buffer at all; a 1km search found 1431 water pixels centred 12.9122/77.6727, roughly 450m northwest of the guessed 12.9081/77.6773. So that row measured land beside the lake, not the lake. Two lessons: a restored *lake* shows up in MNDWI (water extent) and in the NDVI of its planted rim, not in NDVI at its centre; and coordinates must be verified, not recalled — Kasavanahalli and Harlur lakes are within the same 1km, so even the water centroid may blend basins.

- 2026-09-07 — **M1 results. Loss confirmed against a control; gain not established.** Sites are now OSM polygons pinned by id (`fetch_sites.py` → `data/osm_sites.geojson`), not hand-typed points, and each is probed with the index that can see its expected change. The raw series overstated the case — Varthur's 0.339 (2017) → 0.210 (2026) leaned on a year excluded as thin, and on the solid 2019-2026 run the raw decline is only -0.055 against a +0.051 single-year wobble, i.e. trend indistinguishable from weather. **Differencing against Lalbagh fixes this**: Varthur - Lalbagh goes -0.193 → -0.266 (-0.073), the largest single-year wobble falls to +0.015, and the decline is flat at ~-0.18 until 2023 then monotonic through 2024-2026. So the loss is real, ~5x the noise, and *recent* — a sharper claim than the raw series supports. Verdict: flat ✓ (Lalbagh, the control), loss ✓ (Varthur), gain ✗ — the rim differences to only +0.024 over the run, less than its own +0.034 year-to-year wobble.
- 2026-09-07 — Kaikondrahalli lake MNDWI reads -0.12 to +0.33, low and noisy for open water, which should sit well above +0.3. Worth one look before trusting MNDWI at M3 — likely water hyacinth reading as vegetation, or the OSM relation including shoreline. Not chased yet.
- 2026-09-07 — Geocoding is its own trap, distinct from gotcha 7. "Lalbagh Botanical Garden" resolves to a different botanical garden 20km away in Doddaballapur; a bare "Lalbagh" resolves to a railway station; the real object is `way/15802464`, named "Lalbagh Botanical Gardens" (plural). Sites are therefore pinned by OSM id with a bounding-box assertion, so a rename upstream fails loudly instead of silently relocating a site.

- 2026-09-08 — Session paused here. M0 closed and M1 run; the open items are the three decisions in Status, not missing work. Uncommitted at pause: `fetch_sites.py`, `spot_check.py`, `results/m1_spot_check.csv`, and the PROJECT.md edits. `data/osm_sites.geojson` is gitignored and regenerates from `fetch_sites.py` in one call, so it does not need committing. Also settled this session, for anyone re-reading the early entries: the EE project id is recorded in Status, and the account is the personal Gmail.

- 2026-09-11 — **Ring test run; the missing gain is not a dilution artefact.** `spot_check.py` now
  probes the Kaikondrahalli rim at 50m, 100m and 200m in one pass, so dilution by the surrounding
  Sarjapur corridor would appear as a gradient. It doesn't. Differenced against Lalbagh over
  2019-2026 the three rings run +0.030 / +0.033 / +0.024, against max single-year wobbles of
  0.036 / 0.039 / 0.034 — run <= wobble at every radius, and not even monotonic in radius. Smoothing
  to 3-year means (2019-21 vs 2024-26) leaves +0.010 / +0.020 / +0.012. The absolute level does fall
  with radius as expected (-0.15 / -0.20 / -0.24; the rim is greener nearest the lake), so the rings
  are genuinely reading different ground — it is the *trend* that is absent, not the contrast.
  **Decision 3 closed:** the 200m ring was not cancelling a gain.
- 2026-09-11 — MNDWI over all three rings is flat at -0.33 to -0.40 across 2019-2026 and does not
  rise as the ring narrows, so the flat NDVI is not water or hyacinth bleeding into the rim. This
  also narrows the 09-07 note about noisy lake MNDWI: the noise is inside the lake polygon, not in
  the rim. (The lake's own 2026 reading, 0.327, is the highest in the series against 0.074 in 2024 —
  a single-year spike on a noisy line, not a trend, and not enough to claim a blue gain.)
- 2026-09-11 — **Best read on the gain direction: the restoration predates the window.** Flagged as
  unverified — Kaikondrahalli's restoration date has not been checked against a source, and under
  gotcha 7's spirit a recalled date is worth no more than a recalled coordinate. But it is what a
  flat, uncontaminated rim at every radius means. Consequence: don't spend another session guessing
  a second restored site. M2's change layer ranks hexes by gain, so the gain direction can be closed
  from data instead of from memory — with the caveat that picking the story after seeing the ranking
  is confirmation-shopping, so fix the selection rule (top-N gaining hexes) before looking.
- 2026-09-11 — `results/m1_spot_check.csv` is still the only copy of the M1 numbers and is still
  untracked. The re-run overwrote it in place; nothing was lost only because the 200m rows
  reproduced exactly. Commit `results/` before the next parameter change, or it destroys a
  deliverable the 09-06 gitignore entry already flagged as one that should be tracked.

- 2026-09-11 — **Imagery pulled for every year; `getThumbURL` specifically works on the reduced
  scopes.** Narrow claim, deliberately: thumbnails go through the plain `earthengine` scope, so the
  09-06 Drive/GCS block does not cover them. `Export.image.toDrive` and GCS export were *not*
  retested and are presumed still blocked; M5/M6 need real raster tiles, not 700px thumbnails, so
  the documented fix there (register an own OAuth client id) stands untouched. `render_sites.py` writes `results/imagery/` (42 frames, 7.8 MB, true colour +
  greenness, fixed stretch, measured geometry outlined) and `build_contact_sheet.py` turns it into
  `results/imagery/index.html`. This is now the cheapest way to falsify a number by eye.
- 2026-09-11 — **The loss is not water contamination — checked, not assumed.** The Varthur greenness
  frames show the lake reading as *dense vegetation* in 2017-2020 (NDVI 0.65-0.82: water hyacinth,
  not trees), so if the fixed OSM lake polygon under-covered the moving water edge, weed mat would
  leak into `varthur_built` and its collapse would masquerade as canopy loss. Measured: water pixels
  inside `varthur_built` are 0.1-0.3% in every year and weed-mat pixels are 0.0% throughout. The
  exclusion holds. **The loss verdict survives this.**
- 2026-09-11 — **New and stronger than anything else in M1: the 150m ring just outside Varthur
  lake.** Differenced against Lalbagh over 2019-2026 it runs -0.023 → -0.209, slope -0.0242/yr,
  t = -9.23 — roughly triple the strength of the whole-area loss (t = -3.18) on the same eight
  points. It survives without the control too (raw slope -0.0205/yr, t = -7.53), which none of the
  other series manage. **Caveats, both mine to own:** the ring is carved out of `varthur_built`, so
  it is a *sub-region of* the headline number, not an independent site — expect correlation, and do
  not quote the two as if they corroborate each other. And the decline is not strictly monotonic:
  one reversal, 2022 (-0.116 → -0.102). The read is the lake's immediate rim being built over.
  Candidate headline for M2, and it mirrors the Kaikondrahalli rim that refused to show a gain —
  same probe, same 150-200m scale, opposite result, which is itself evidence the probe can see
  change when change is there.
- 2026-09-11 — **Varthur lake flipped from hyacinth to open water.** Its own NDVI runs 0.820 (2017)
  → 0.119 (2026) and water-pixel share 4.5% → 57.6%, MNDWI -0.369 → +0.112. Visually unmistakable in
  the 2019 vs 2026 greenness frames. **Do not bank this as the missing gain yet:** Kaikondrahalli's
  MNDWI also spikes in 2026 (0.104 → 0.327), and two unrelated lakes both jumping in the same year
  points at shared hydrology — 2025 monsoon carry-over — rather than two independent restorations.
  Same common-mode trap as the Lalbagh-subtraction argument, one level up. **The cheap
  discriminator, for whenever this is picked up:** the two lakes are ~4km apart and both inside the
  Sarjapur/Varthur corridor. Probe a third water body well outside it — if that one also peaks in
  2026, it is regional hydrology and neither lake is a restoration story.
- 2026-09-11 — Cloud metadata retrieved while rendering, which retires a standing worry: the thin
  years are *clear*, not hazy. 2017 is 4 scenes at 0.0% cloud, 2018 is 7 at 6.8% mean. The cloudiest
  years are 2020-2023 (17-25% mean, individual scenes to 100%), all with n>=24 where the median
  absorbs it. So thin-sample years are a precision problem, not a haze-bias one. `spot_check.py`
  still applies no cloud mask at all — unchanged, and still worth adding before M2.
- 2026-09-11 — `results/imagery/` is 7.8 MB of untracked JPG/PNG. `.gitignore` blocks `*.tif` but
  not `.jpg`/`.png`, so a bare `git add results/` would commit all 42 frames. Undecided by design —
  Aditya's call whether the frames are a deliverable or scratch. `index.html`, `manifest.json` and
  the two scripts are cheap and should be kept either way, since the frames regenerate from
  `render_sites.py` in one command.

- 2026-09-11 — **`notebooks/m1_spot_check.ipynb` added — the measurement, step by step, runnable.**
  Aditya's call, and the right one: the scripts printed answers without showing the chain, which
  made a five-step arithmetic pipeline feel like a black box. The notebook walks shape → available
  photos → per-pixel median → the NDVI division → the spatial mean, with one cell computing a single
  pixel's greenness by hand and asserting it equals Earth Engine's (`0.544341` both ways). It then
  lays out the control-subtraction argument with the trend fits, and ends on the weed-mat
  contamination check. The 150m Varthur ring is computed *inside* the notebook rather than quoted
  from this log, so its fits table derives the t = -9.23 itself. Executed end to end; all figures reproduce the numbers logged above.
  Scripts stay as the pipeline — the notebook is the thinking surface, not a second source of truth.
- 2026-09-11 — Deps added for it: `jupyterlab==4.6.3`, `matplotlib==3.11.1`, plus
  `nbconvert==7.17.1` and `nbformat==5.11.1` — the last two pinned explicitly because they are what
  *executes* the notebook headlessly, and leaving them transitive is exactly the trap this project's
  long idle gaps set. `ipykernel` still comes in transitively. Note the committed notebook is ~1.5 MB because outputs
  (7 embedded figures) are stored inline — that is deliberate, so it reads correctly without a live
  EE session, but it does mean every re-execution produces a large diff.
- 2026-09-11 — Two bugs worth not rediscovering when generating `.ipynb` files programmatically:
  `source` lines must each retain their trailing `\n` (a bare `split("\n")` concatenates the whole
  cell into one unparseable line), and `FeatureCollection.getInfo()` returns a **dict** — iterate
  `["features"]`, not the result. Both failed loudly at execute time, which is the good case.

- 2026-09-11 — **Year range decided: 2019–2026.** Eight dry seasons, n>=12 photos every year. Text
  sweep applied to the title, the scope row, M2 and M6. 2017–2018 stay in tables as thin context;
  2016 is dropped entirely (1 scene, wrong tile).
- 2026-09-11 — **A per-year water mask is strictly worse than no mask. Do not build one.** Hyacinth
  is invisible to MNDWI: over Varthur lake the wetness reading is -0.33 to -0.43 — indistinguishable
  from dry land — in every hyacinth year, and only goes positive (+0.112) in 2026 once the mat
  clears. So masking "pixels that read as water this year" would retain the 0.74 greenness
  hyacinth years and delete the 0.12 open-water year, manufacturing exactly the upward trend the
  mask was meant to remove. The obvious fix is disqualified; only a **static** footprint mask is
  admissible.
- 2026-09-11 — **The aggregate half of the contamination worry does not hold — measured, and it came
  out backwards.** Over a 2700 km² Bangalore box, JRC Global Surface Water puts the lake/tank
  footprint at 24.8 km² (0.92% of area) at >=25% occurrence. Lake beds average 0.05–0.18 greenness
  against a land mean of 0.26–0.32, i.e. **below** it, so water drags the city figure *down* by
  0.0009–0.0025 and masking it changes the city trend from +0.00163/yr to +0.00173/yr. At hex and
  city scale this is a rounding error, and its sign is the opposite of the one feared.
- 2026-09-11 — **The visualization half of the worry is real and is a sign error, not a bias.** The
  swipe layer is per-pixel at z14, not a regional mean. A 1km hex containing Varthur lake is ~10%
  lake by area; the lake swings 0.82 → 0.12, moving that hex by ~0.07 — comparable to eight years of
  genuine canopy change, and rendering as canopy **loss** on the one map where a cleared lake is a
  restoration success. Two conclusions worth keeping separate: the mean is fine, the map is not.
- 2026-09-11 — **Cost of the static JRC mask, checked rather than assumed.** `JRC/GSW1_4` occurrence
  covers 1984–2021, so it is a historical footprint and will mask land that is no longer water. Of
  the >=25% footprint in Feb–Mar 2026: 62.5% still reads as water, 25.9% is vegetated (weed mat,
  marsh, or a tank since built over and re-greened) and 11.6% is dry or built. Tightening to >=50%
  raises the still-water share to 72.1% but shrinks the footprint to 9.9 km², missing shallower
  tanks. So the mask erases roughly a tenth to a third of its own area from the loss layer — and
  built-over tanks are precisely the loss M4 exists to find. **Scope note for M2:** mask by static
  footprint, cross-check it against OpenCity's current lake inventory (already a listed data
  source) rather than trusting JRC alone, and carry a masked-pixel count per hex so any hex whose
  value depends on the mask choice is visible instead of silently folded in.

- 2026-09-11 — **Decided: no lake masking. Skipped deliberately, not overlooked.** *(Read with the
  2026-09-20 entry: that decision stands unchanged for the city mean — it is a decision about
  masking pixels — and is what makes the later hex exclusion consistent rather than a reversal.)* It moves the city
  mean by 0.002 and the trend by 0.0001/yr, and it would cost a static-footprint pipeline, an
  OpenCity cross-check and a per-hex masked-pixel count — while erasing 11–26% of its own area from
  the loss layer, built-over tanks included, which is the very thing M4 exists to find. Residual
  exposure is confined to lake-containing hexes appearing as fake canopy loss in the M6 swipe and
  any "biggest change" ranking. **Mitigation, and it is not a pipeline feature:** eyeball the top-N
  changed hexes against `results/imagery/`-style frames before promoting any of them into the story.
  Revisit only if a lake hex actually reaches a headline.
- 2026-09-11 — **There is no detectable city-wide greenness trend over 2019–2026, and this is a
  result worth not misreading.** Fitted slope +0.00163/yr, standard error 0.00403, t = 0.40. The 95%
  range runs -0.00823 to +0.01149 per year, i.e. -0.058 to +0.080 over eight years — it spans zero.
  The fitted 8-year total (+0.011) is five times *smaller* than a typical single-year jump (0.054),
  and Lalbagh swings 0.056 across the same window while not changing at all. So the series is
  rainfall, not canopy. **The +0.00163 figure is only usable as a difference** (with water masked it
  is +0.00173, i.e. masking changes nothing) — quoting it as a level would assert a city-wide
  greening this data cannot support. This is the same absolute-vs-relative boundary raised against
  the Lalbagh subtraction, now measured directly at city scale, and it is the strongest argument yet
  for the project's relative framing.

- 2026-09-11 — **Order of operations pinned down in the notebook, and 2016's real problem named.**
  M1 averages each year over the shape and *then* subtracts years (average-then-subtract). The
  alternative — difference each pixel across years, then average — returns an identical answer
  (-0.054602 both ways, gap 5.67e-15), because the mean of differences is the difference of means.
  **That equivalence holds only while both years cover the same pixels**, and coverage was checked:
  every year from 2017 on has all 78,469 pixels inside `varthur_built`. 2016 has **2,234, i.e. 2.8%**
  — the single scene sits on tile 43PHQ and clips one corner. So 2016's 0.274 is not a thin
  measurement of Varthur, it is a measurement of *different ground*, which is a stronger reason to
  drop it than sample size and supersedes the softer "thin" wording used earlier.
- 2026-09-11 — Consequence for M2: the per-pixel difference image is the deliverable, not an
  implementation detail. Averaging is the last step, not the method — the swipe layer, the hex
  aggregates and any "biggest change" ranking all derive from that image. The notebook now renders
  it for Varthur as a one-neighbourhood preview of M2, and it shows gain and loss pixels sitting
  side by side inside a polygon whose single summary number is -0.055.

- 2026-09-11 — **M1 closed on a 2-of-3 gate; M2 scope clarified to three layers.** The gain
  direction is closed by decision rather than evidence, and that is recorded as such. Also settled:
  the endpoint-vs-slope tension is not a conflict — endpoint differencing is fine for *rendering the
  change map* and wrong for *quoting a figure*, which is the distinction that had been blurred.
  And the "city-wide score" question is struck rather than answered: it was already ceded to IISc in
  the scope table, and the 2026-09-11 measurement shows there is no readable number there anyway.

- 2026-09-11 — **M2 step 0 done: boundary and hex grid built.** The GBA boundary turned out to
  already exist in OSM as `R7902476` — `admin_level=7`, `operator=Greater Bengaluru Authority`,
  717.2 km², which matches the delimitation figure. No need to assemble it from the five
  corporations. Plus a 10km ring = **2,174.9 km²**, and **2,868 H3 res-8 hexes** at 0.758 km² mean
  covering 2,173 km², i.e. the grid tiles the boundary with no meaningful gap. **22,944 rows** is
  therefore M2's table size, replacing the ~29k estimate.
- 2026-09-11 — Three conventions fixed in `build_grid.py`, each guarded by an assert that fails
  loudly, following `fetch_sites.py`'s precedent: the boundary area must land in 650-800 km² (so an
  upstream OSM edit breaks the build rather than silently moving the study area), the hex count must
  land in 2000-4500, and hex centres must fall inside Bangalore's lat/lng box — that last one exists
  because h3 v4 is latitude-first while GeoJSON is longitude-first, and a silent swap yields a
  perfectly valid cell set over the wrong hemisphere. Verified empirically that
  `h3.geo_to_cells` reads a shapely `__geo_interface__` correctly, so no manual flip is needed.
- 2026-09-11 — **Hex membership is by centre, and this is deliberate — do not "fix" it by clipping.**
  Hexes straddle the boundary edge. The 10km ring is self-defined so its edge carries no meaning,
  and clipping would leave edge hexes with fewer pixels than the rest for no analytical gain. The
  10km buffer outline is also simplified at 10m (one pixel), cutting 282 vertices to 203 — that
  polygon is serialized into every Earth Engine request for the rest of M2, so its size is not free.

- 2026-09-11 — **M2 step 1 done: the hex table exists and agrees with M1.** 22,944 rows, no
  duplicates, no nulls, pixel counts near-constant (7,966-8,042, zero hexes varying >5% across
  years, zero with a cloud gap). **The independent check that matters:** the 12 hexes whose centres
  fall inside the Varthur study polygon give slope -0.0140/yr, t = -2.62 against the city median —
  against M1's -0.0119/yr, t = -3.18 against Lalbagh. Different geometry, different control, same
  answer. That is the first time M2 machinery has been confirmed by something outside itself.
  `wet` (MNDWI) was captured in the same pass, so M3's blue layer needs no re-run.
- 2026-09-11 — **A single hex is not a site, and the naive cross-check misleads.** The hex containing
  Varthur's centroid reads 0.148-0.200 and the hex containing Lalbagh's reads 0.308-0.347, against
  M1 polygon values of 0.21-0.27 and 0.44-0.50. Neither is an error: Varthur's centroid hex sits
  mostly *on the lake*, and Lalbagh (1.4x1.1 km) is smaller than a 0.758 km² hex so its hex is
  mostly surrounding city. Compare like with like — aggregate the hexes covering a region, don't
  pick the centroid's hex.
- 2026-09-11 — **Two bugs worth not repeating, from the first run hanging after 2.5 years.** The
  Earth Engine client sets **no socket timeout**, so a dropped connection blocks forever; the retry
  loop never fired because a hang raises nothing, and the process sat at 0% CPU for 30 minutes
  looking exactly like slow progress. `socket.setdefaulttimeout(180)` converts it to a catchable
  exception. Separately, a watcher built on `pgrep -f measure_hexes.py` matched *its own* command
  line and would never have exited. Diagnose a suspected hang by CPU time, not elapsed time.
- 2026-09-11 — The composite is **not** clipped to the study boundary and does not need to be —
  `reduceRegions` only reads inside a hex, so the boundary's only job was choosing which hexes
  exist. Effective study area is the union of hexes (2,173 km²). Earlier wording in M2 said
  "clipped to the boundary"; that describes intent, not the implementation.

- 2026-09-16 — **`notebooks/m2_hex_table.ipynb` added: the hex table looked at before any
  normalisation.** Six figures over `results/m2_hex_table.csv` — per-year distributions, the 2019
  and 2026 choropleths, the endpoint-difference map, the M1 cross-check, and `wet`. Unlike
  `m1_spot_check.ipynb` it touches **no Earth Engine and needs no auth**, so it re-runs offline.
  Deliberately descriptive: no per-hex slopes in it, because those are step 2a and writing them
  twice invites the two copies to drift.
- 2026-09-16 — **Pixel counts are identical across all eight years, for every hex, to the pixel.**
  `measure_hexes.py` was written to tolerate ±5% and logged 7,966–8,042 as the range; that range is
  *between* hexes. Within a hex the count does not move at all, so there is no cloud gap anywhere in
  the table and every year-to-year comparison in it is the same ground measured twice. Stronger
  than the tolerance the script was built around.
- 2026-09-16 — **City trend re-derived from the hex table: +0.00115/yr, t = 0.29** against the
  logged +0.00163/yr, t = 0.40. Not a discrepancy — the logged figure is pixel-weighted over a
  2,700 km² box, this one is the unweighted mean of 2,868 hex means over 2,173 km². Same conclusion:
  no readable city-wide trend. Also measured directly: the 2019→2026 endpoint difference (+0.022) is
  **three times** the fitted 8-season total (+0.008), which is the endpoint-vs-slope rule with a
  number on it.
- 2026-09-16 — **The Varthur cross-check was understating itself: one of the 12 hexes holds 40% of
  Varthur lake.** Removing that hex gives −0.0095/yr at **t = −3.73**, against −0.0138/yr at
  t = −2.62 with it. Smaller slope, much less scatter, and it is the fairer comparison because M1's
  `varthur_built` polygon had the lake punched out by construction (−0.0119/yr, t = −3.18). So the
  logged 12-hex figure understates the M1/M2 agreement rather than overstating it. Use the
  11-hex number when quoting this check.
- 2026-09-16 — **The lake-contamination exposure accepted on 2026-09-11 is confirmed, not
  hypothetical, and it is worse than "some hexes".** Ranked by absolute 2019→2026 greenness change,
  the four largest losses in the grid all show wetness climbing as greenness collapses; three of
  them swap sides in a single year (2023 for two adjacent hexes in the north-west, 2026 for
  Varthur). Of the top 20 losses, **10 end wetter than −0.2 against a city median of −0.454, and 18
  of 20 got wetter over the run.** *(Corrected 2026-09-20: the second half of that sentence is an
  artefact — see below. The first half survives a proper null and the conclusion is unchanged.)* An
  absolute top-N loss list is not a canopy-loss list, it is a water-arrival list wearing one. The identities of those hexes are **not** established and must not
  be guessed (gotcha 7); what is established is the signature. This was reached before the ranking
  existed rather than after, which is what the mitigation asked for.
- 2026-09-16 — **MNDWI at hex scale is mostly measuring "not vegetated", not water.** Across hexes
  it correlates **−0.65** with greenness, and the dark band on the wetness map is the built-up core
  because dry vegetation reflects shortwave infrared strongly. Only **5 hexes of 2,868** read
  positive at all; above that threshold it does mean real water (Varthur's lake hex, at 40% of one
  cell, reaches +0.383). So `wet` does two different jobs at the two ends of its range and only one
  is the job it was chosen for. **M3 will need the water test applied per pixel and then counted**,
  not the pixels averaged and the average tested — the same average-then-threshold question M1
  settled for greenness, landing this time where the two do *not* commute. Does not block M2.

- 2026-09-20 — **The 2026-09-16 wetness evidence was two statistics and only one of them was real.**
  *18 of 20 largest losses got wetter over the run* is **retired**: greenness change and wetness
  change correlate at **−0.691** across hexes, the top-20 losses sit at z = −6.35 on greenness
  change, so the correlation alone predicts essentially 20 of 20. Observed 18 is slightly *under*
  expectation. Selecting the biggest losses selects hexes that got wetter by construction. *10 of 20
  end wetter than −0.2* **survives**, and needed a better null than the one first used: the naive
  1.2% base rate is the same mistake, because low-green hexes read wet anyway. Matched on 2026
  greenness the expectation is 2.14 of 20 against 10 observed — **4.7×**. The discriminator is the
  **absolute end-state level, never the change.**

- 2026-09-20 — **The guard had to be symmetric, and the gain list is why.** Hyacinth is invisible to
  MNDWI (2026-09-11), so open water in 2019 that goes under a weed mat by 2026 reads as greenness
  climbing from nothing to dense canopy — a fabricated restoration, with the wetness evidence in the
  *first* year and gone by the last. Measured: **7 of the 20 largest gains start wetter than −0.2**,
  and a final-year-only guard catches 4 of them. This matters more than the loss side, because M1
  closed the gain direction *by decision* on the promise that M2's ranking would surface a real
  restoration if one existed.

- 2026-09-20 — **Decided: rule C. A hex is water if it reads wet (MNDWI > −0.2) in ≥2 of the 8
  years, or in either endpoint year.** 50 hexes, 38 km², **1.7%** of the grid. Excluded outright
  from the greenness study, Aditya's call, rather than flagged. Why not the simpler tests: a
  **single baseline year cannot work** — the best year catches 39 of the 56 ever-wet hexes and 2019
  catches 18, because water in this city is not a fixed object (only **7 hexes read wet in all
  eight years**), and hyacinth hides Varthur from MNDWI in every year before 2026. **≥2 years alone
  is blind at the edges** — 7 of the 14 single-year hexes fire in 2026, and all 3 single-year hexes
  reaching the top-20 loss list are among them; 2026 has no 2027 to corroborate it. The endpoint
  clause is justified by that asymmetry, not by its catch rate against an endpoint-sorted ranking,
  which would be circular. **The independent check:** scored against a *slope*-ranked top-40, which
  privileges neither endpoint, rule C catches 13 against rule A's 13 and rule B's 10 — C recovers
  the strict rule's full protection while sparing 6 genuine mid-run blips.

- 2026-09-20 — **This does not reverse the 2026-09-11 no-masking decision, and the log must not be
  read as if it does.** That decision was about masking *pixels* to correct the *city mean*, and it
  was measured and rejected because the mean moves by 0.002 while the mask erases 11–26% of its own
  area — built-over tanks included, which is M4's target. This is a *hex* exclusion from the
  *ranking*. The two are consistent, and the 09-11 measurement is what makes them so: removing the
  water hexes shifts the normalisation reference by at most **0.0009** in any year against
  year-to-year swings of 0.05, and leaves the city trend unreadable (+0.00115/yr t = 0.29 →
  +0.00141/yr t = 0.35), reproducing the pixel-scale +0.00163 → +0.00173 by a different route. The
  exclusion is not moving the baseline; it only removes contaminated entries. **The excluded 50 are
  kept, not discarded — they are M4's candidate set**, since a tank that became buildings is the
  loss M4 exists to find.

- 2026-09-20 — **`results/m2_water_hexes.csv` is the single source for the exclusion.** 50 rows with
  `h3, n_years_wet, wet_2019, wet_2026, peak_wet, caught_by` (32 caught by both clauses, 10
  recurrent-only, 8 endpoint-only), so the rule is auditable per hex. Step 2a reads that file and
  does **not** re-derive the rule — the same reason the 09-16 notebook kept slopes out of itself:
  two copies of a selection rule drift. `m2_hex_table.csv` is untouched at 22,944 rows; the
  exclusion is a downstream filter, so it stays reversible and visible.

- 2026-09-20 — Notebook section 7 added and the whole notebook re-executed; the figure title and the
  printed 18-of-20 line in section 6 were amended in place so the notebook no longer argues with
  itself. Study size for everything downstream is now **2,818 hexes / 22,544 rows / 2,135 km²**.

- 2026-09-21 — **A flat subtraction is the right correction, and this is now measured rather than
  assumed.** Aditya's question: if the city median under-corrects the green belt, and the green belt
  is where loss is expected, does the method miss the loss? Measured: hexes do *not* respond to
  weather equally — regressing each hex's deviation on the city's, **β runs 0.53 in the least-green
  decile to 1.31 in the greenest, a 2.5× spread**. So a flat subtraction over-corrects built-up
  hexes and under-corrects green ones. **But the leftover is a wobble, not a bias:** it peaks at
  0.010 with a trend of +0.00044/yr, against real losses of 0.13–0.31, because the city series it is
  a fraction of has no trend (t = 0.29). Under-correction makes a green hex's line *fuzzier*, not
  its loss smaller. **The error runs opposite to the worry** — fuzzier lines throw more extreme
  slopes by chance, so the green belt is over-represented at the top of a ranking, not missed by it.

- 2026-09-21 — **Three normalisation schemes pick the same hexes, so the choice is closed.** Top-40
  agreement: additive (subtract the city median) vs β-residualised **38 of 40**; additive vs
  stratified-median **36 of 40**; β-residualised vs stratified **35 of 40**. Keep the additive
  subtraction already specified for 2a — confirmed, not assumed. Do not spend a session choosing
  between corrections that select the same ground.

- 2026-09-21 — **Baseline choice is itself a trap, and it bit once before being caught.** β was
  first computed against each hex's 2019 value and read 0.65 → 0.95 (1.5×) — flattened and nearly
  flat. The yearly weather deviations sum to zero by construction, so a hex's **8-year mean carries
  no weather**, while any single year does; 2019 is the driest year in the run, so a weather-
  sensitive hex reads low in it and lands in a lower decile, suppressing the very relationship being
  measured. Correct figure is 0.53 → 1.31 on the 8-year mean. Same class of error as the statistic
  section 7 retired: a selection variable quietly correlated with the thing being measured. **For
  the top-40 composition question the contamination runs the other way** — a hex that lost half its
  canopy has an 8-year mean midway between its start and end state — so that result is reported
  under both baselines and holds under each.

- 2026-09-21 — **Stated limit for publication: this ranking cannot see the built-up core.** The
  least-green decile contributes **0 of the top 40**; the greenest contributes **9**. Below 0.22
  greenness — 379 hexes, 13.4% of the grid — only 3 reach the top 40, about half their share. Not a
  normalisation failure: a hex at 0.16 greenness has less available range than a farmland hex has
  year-to-year scatter (residual scatter 0.016 vs 0.031). **So M2 answers "where did vegetated land
  lose its vegetation", not "where did the city lose its remaining trees".** Those are different
  questions and only the first is answerable at 0.758 km² on 10m pixels. Put this in the published
  text rather than letting a reader find it.

- 2026-09-21 — Normalisation removes what it was meant to: the spread of the yearly medians falls
  from **0.0663 to 0.0055**. The endpoint map and the normalised-slope map correlate +0.904 but
  **402 of 2,818 hexes move by more than 20 percentile points** between them, which is the visual
  case for not quoting endpoint figures.

- 2026-09-23 — **Correction to the entry above: the 402 hexes move because of the *measure*, not the
  weather.** Subtracting the city shifts every hex by the same amount, which changes no ranks and no
  correlation. So endpoint-vs-slope ranking differences come entirely from end-minus-start vs the
  trend line. The +0.904 is identical whether or not the endpoint is normalised.

- 2026-09-23 — **Trend line vs end-minus-start, measured on a clean step** (`m2_hex_table.ipynb`
  section 9). A one-year drop of 0.20 reads as 0.117 on the trend line when it happens in the first
  or last year and 0.267 in the middle, a 2.3× range set purely by timing; end-minus-start reads 0.200
  in every case. The two top-40 lists share 28 of 40. **Decided (Aditya): rank by end-minus-start.**
  Its cost is that it ignores the years between; that cost looked large on hex C until the deep dive
  showed C's end years were real ground, not luck.

- 2026-09-23 — **Deep dive on three hexes** (`m2_hex_deep_dive.ipynb`). None was random; every jump
  matched something visible on the ground. **B** (`88601696e3fffff`, Shivaram Karanth Layout) is clean
  clearing for a layout in 2024. **A** (`8860169631fffff`, Attur Lake, 15% lake): 89% of its
  2025→2026 drop and 54% of its 2019→2026 drop comes from pixels that became open water. Water
  arrived; whether that is restoration or a wet year is not established. **C** (`8861892501fffff`) is
  **50% Bellandur Lake and 33% K&C Valley sewage plant**, not farmland as first guessed: marsh, dug up,
  regrown, dug up again (OSM notes "rejuvenation and desilting ongoing as of 2026"). Ruled out as
  causes: the normalisation (hex swings 0.18–0.21 raw against the city's 0.064) and clouds (the
  clear-pass median matches the stored value within ~0.03). C shows 0–3% open water while being half
  lake, which is exactly how rule C misses weed-covered lakes.

- 2026-09-23 — **Rule C leaked badly.** Against every OSM lake, pond, wetland, sewage pond and
  reservoir in the study area (`fetch_water.py`, 6,421 polygons), **25 of the top 40** by
  end-minus-start were lake hexes (≥10% mapped water), against 9.7% of the grid: 6.5×. The trend-line
  top 40 was similar (22). Rank 2 was a hex that is 99% Hesaraghatta Lake. Mapped water is **3.95% of
  the study area** (lakes 3.3%, wetland 0.55%, reservoirs 0.11%, sewage ponds 0.01%), spread across
  lake edges. 46 of rule C's 50 hexes have ≥10% mapped water; the other 4 are an unmapped tank bed
  near Hoskote (Shankanipura/Upparahalli) that the pixel mask won't catch.

- 2026-09-23 — **Decided (Aditya): pixel mask from OSM water, replacing rule C, wetlands kept.**
  One approach, not two. Wetlands stay in the measurement because their loss belongs in the story, and
  OSM maps them too patchily to mask consistently (136 of 155 carry no subtype, 2 are named, 63% of
  their area sits within 50 m of a lake). The mask is fixed across years, so this is **not** the
  per-year mask the 2026-09-11 entry disqualified. Masking is exact: land-pixel counts match OSM area
  within 0.5% on four test hexes.

- 2026-09-23 — **What the mask changed** (`m2_masked.ipynb`). Hexes with no mapped water didn't move
  at all. Lake hexes in the top 40: 25 → **19**; wetland ≥10%: 7 → 10. Hex B rose from 72nd to 51st;
  A fell 20 → 83; C fell 10 → 72; the 99%-Hesaraghatta hex fell 2 → 194. New arrivals at the top are
  mostly lake *shorelines*, and hexes rule C used to drop entirely.

- 2026-09-23 — **Photo check on the masked top 12** (`m2_top_photo_check.ipynb`). **7 of 12 are real
  clearing or building**: the Shivaram Karanth Layout in Yelahanka (ranks 6, 9, 10) and a development
  area east of Whitefield around 13.015, 77.74–77.76 (ranks 2, 5, 11, two of them with mapped wetland
  built over), plus spreading buildings north of Ramapura (8). The rest: rank 1 Hennagara Lake, where
  OSM maps only a sliver of the lake and 9–42% of the "land" is water; ranks 7 and 12, slivers with
  almost no land; rank 3, Ramapura lake works on the wetland edge; rank 4, farm plots beside
  Hesaraghatta (crop swings). Only 2 of 12 had open water inside their unmasked land in any year.
  **Hesaraghatta's OSM outline is good:** it is the full 5.98 km² bed; water filled 2% of it in
  2019–21 and 40–52% from 2023, with only 0.02–0.27 km² outside it. The problem there was a dry lake
  bed reading as grassland then flooding, which the mask now removes.

- 2026-09-23 — **Decided (Aditya): apply a 25% minimum-land cutoff, and carry a "land without water
  or wetland" column as a review flag only.** The cutoff removes exactly the two slivers in the top
  12. The flag marks hexes where lake-side wetland may distort the number, for case-by-case checking;
  wetland is still measured. **Implemented** in `m2_masked.ipynb` section 6: 8 hexes fall under
  25% land and are not ranked (both slivers among them); 18 of the new top 40 are flagged. In the photo-checked
  top ten the flag caught every doubtful hex (Hennagara, Ramapura works, Hesaraghatta farm plots) and
  also flagged three real losses where wetland was built over, which is why it stays a flag.

- 2026-09-23 — Earth Engine hangs are a pattern, not a one-off: `socket.setdefaulttimeout` does not
  stop them. The masked run stalled twice (2022, 2024) and resumed cleanly each time. A notebook run
  hung for 21 minutes until `ee.data.setDeadline(120_000)` plus a retry wrapper was added. Use both in
  any new EE code. Overpass is flaky too: `overpass-api.de` returns 504 for per-hex polygon queries.
  `overpass.kumi.systems` works but can take a minute, and returns relations without member geometry
  under `out geom tags`; Nominatim's lookup with `polygon_geojson=1` is the reliable way to get a
  lake outline.

- 2026-09-23 — The two Earth Engine notebooks store their photo figures as JPEG, re-encoded after
  execution: `m2_top_photo_check.ipynb` went from 16.5 MB to 2.7 MB, the deep dive from 4.9 to 1.0 MB.
  A plain re-run writes PNG again, so re-encode before committing, or the repo grows by about 20 MB
  per run.

- 2026-09-26 — **Decided (Aditya): from Dynamic World, use only the "trees" class**, as a second way
  to measure green loss on the same hexes. "This area had many trees and now has few" is the story;
  crops or scrub cleared for a layout is not the green-cover loss this project is about. Rank the
  whole city by tree-share change, not just the greenness top 15, and compare the two one-to-one.

- 2026-09-27 — **`measure_trees.py` → `results/m2_hex_trees.csv`: Dynamic World tree share per hex
  per year**, Feb-Mar mode label, same hexes and years as the greenness table. One pass writes both
  `trees_land` (the same OSM water mask as `--mask-water`, the default) and `trees_all` (no mask).
  Pixel counts match the masked and unmasked greenness tables exactly for every row, so the two
  methods measure the same ground. The run took about 13 hours: 2020, 2021, 2022 and 2024 each
  stalled for over an hour **even with** `setDeadline` and the socket timeout set, and resumed.
  Budget for that on any whole-city Dynamic World run.

- 2026-09-27 — **The tree ranking does not hold up as a separate list yet.** Measured:
  - It overlaps the greenness top 40 by only 5 of 40. Rank agreement across all 2,860 hexes is 0.60.
  - **Moving the start year by one changes 23 of the tree top 40; greenness keeps 32 of 40** under
    the same test (four start/end definitions: 26-19, 26-20, avg 25-26 minus avg 19-20, avg 25-26
    minus avg 20-21). So most of the instability is Dynamic World's. Greenness has a smaller version
    of the same 2019 problem (the 09-27 photo-check entry below); the end-minus-start decision stands.
  - 20 of the tree top 40 sit east of 77.8°E (the Hoskote side), which is only 221 of 2,860 hexes.
    That band reads 25.9% trees in 2019 against 17-22% in every later year, while the rest of the
    city reads 12-13% in 2019. A regional 2019 anomaly. **Not image count:** 2019 has a Dynamic World
    label for every Sentinel-2 image (12 of 12) at both east points and at three control points
    (Lalbagh, Shivaram Karanth, Hulimangala), the fullest year of all. Cause (weather, crop calendar)
    not checked.
  - City-wide tree share swings by year (11.6% in 2024, 17.0% in 2023). Never use 2024 as an endpoint.
  - 27 hexes stay in the tree top 40 under at least 3 of the 4 definitions; all 27 are also lower in
    2025-26 than in every year 2019-21. 7 of them are in the greenness top 40 (Shivaram Karanth
    Layout, Kolathuru, Thindlu among them). This is the only candidate list worth a photo check.
  - **Photo look at 5 top tree losses:** 1 real clearing (Hegganahalli, bushland scraped for a layout
    — looks like bush, not canopy), 1 partly real (Bhaktarahalli), 2 unclear (Somalapura, Hulimangala),
    1 looks like label noise (Karibeerana Hosahalli, photos unchanged). **None confirmed as canopy.**
    Dynamic World's tree patches are smooth blobs that don't follow visible features at this scale.
    One greenness loss it misses: Varthur (greenness rank 10), dense wetland vegetation cleared for
    construction, tree share 21% → 23%.
  - **It does not fix gotcha 3.** The Hesaraghatta farm-plot hex (`88601694a5fffff`, the doubtful
    crop-swing gain) reads 2% trees to 2021 and 20% by 2026: the same false gain greenness showed.
    With the Grass Farm hex going 15% → 63% trees, the trees label appears to count greener crops or
    grass as trees. Not yet confirmed with photos of that hex.
  - **The lake mask matters less than greenness, but still matters:** 37 of 40 in the tree top 40
    are the same with or without it. Without it, the Hesaraghatta reservoir refilling over its dry
    bed reads as a 26-point tree loss, and Hennagara (lake OSM maps too small) reads as a tree gain
    either way.
  Photos from this look are in the session scratchpad only, not in the repo.

- 2026-09-27 — **Decided (Aditya): Dynamic World is dropped.** It fails all three jobs it was
  brought in for: a second measure of green loss (unstable ranking), telling tree loss from farmland
  clearing (its trees are mostly dark fields and bush in the photos), and fixing crop swings (same
  false gain at the Hesaraghatta farm plots). Carrying it as a column was rejected too: it would need
  its own photo checks and would carry the same weaknesses. `measure_trees.py`,
  `results/m2_hex_trees.csv` and `m2_dynamic_world.ipynb` stay committed as the record, so it isn't
  retried. Gotcha 3 is now handled by eye in the photo checks, and stays a published limit.

- 2026-09-27 — **All 40 biggest losses photo-checked; 30 are quotable** (`m2_loss_photo_check.ipynb`,
  `results/m2_loss_verdicts.csv`, one verdict and a one-line note per hex). Ranks 1-8 carried from
  09-23, ranks 9-40 new. Of the 40: 27 real loss, 3 real loss on wetland, 4 lake works, 6 doubtful,
  0 artefacts. No hex among ranks 9-40 has over 5% open water in its land in any year, so the mask
  plus the cutoff did their job. Findings worth keeping:
  - The Shivaram Karanth Layout is 11 of the 27 real losses, all cleared in one go in 2024. The rest
    are mostly gradual building on the Whitefield-Varthur-Sarjapura side, plus the STRR highway and
    a warehouse at Kolathuru.
  - **The `check` flag finds lake trouble, not farmland doubt:** all 4 lake-works hexes are flagged,
    but so are 9 real losses; the 4 doubtful hexes among the 25 clean ones are all farmland.
  - **Three of the six doubtful hexes (ranks 28, 34, 38) lose over half their drop in the single step
    2019 to 2020 with no visible cause.** The same kind of reading tripped the Dynamic World ranking.
    The site should show 2020 beside 2019, not only the endpoints.
  - **The 2019 bump is in greenness too, on the east fringe.** Relative to the city, greenness east
    of 77.8°E fell 0.032 between 2019 and 2020 alone (about a third of a rank-40 loss); the middle
    band fell 0.007 and the west rose 0.007. With 2020 as the start year, 8 hexes leave the top 40:
    5 of the 6 doubtful hexes (all but the Bellandur shore), the Varthur weed clearing, and 2 real
    losses on the Varthur side (ranks 20 and 23, which fall to 72 and 67). **The photos and the
    start-year test point at the same hexes. 28 of the 30 quotable losses stay in the top 40 either
    way**, and `rank_from_2020` in the verdicts CSV carries this for every hex. The method is
    unchanged; this is a column, not a new ranking.
- 2026-09-27 — **Lake works left out of the headline list (Claude's call, provisional).** Aditya
  asked for M2 to be finished without check-ins, and this was the one editorial call left. Kept on
  the map with the label, left out of the quotable 30: real vegetation removal, but not the
  development story, and quoting it invites an easy rebuttal. Doubtful hexes are left out too.
  Reverse by adding "lake works" to `HEADLINE` in the notebook.
- 2026-09-27 — **Step 2b: the per-pixel change map** (`render_change_map.py` →
  `results/m2_change_map.png`, `m2_change_map.ipynb`). Each pixel is normalised with the same
  city-wide yearly means as the table, so a hex average of the map equals the table: median gap
  7e-16, largest 2e-5 over 40 losses + 60 random hexes. 3,000 px wide went over Earth Engine's 50 MB
  thumbnail limit; 2,800 px (18 m a pixel) is the widest that renders. The PNG is 10 MB, so it is
  gitignored. Three things the site must caption: the core reads faintly brown (the flat-subtraction
  limit from 09-20: -0.014 in the least-green decile to +0.019 in the greenest, a tenth of the
  scale); single fields in the fringe speckle with the crop calendar, so the hex layer should be the
  default view; and the large teal areas are gains that haven't been photo-checked.
- 2026-09-27 — **M2 closed.** Both "done when" items are met: the hex time series over the whole
  boundary, and the per-pixel change layer. Left for later: the gains list photo check, before M7.
- 2026-09-28 — **M3 dropped: the project is green loss only.** Aditya's call. The wetness measure has
  not been reliable at any point: the hex mean of MNDWI correlates -0.65 with greenness and is
  mostly "not vegetated" (09-16), rule C missed weed-covered and seasonally dry lakes (09-23), and a
  per-pixel threshold-then-count pipeline would be new work with no evidence yet that it holds. The
  `wet` column stays in the tables as context. Consequence for M4: its "green/blue → built-up" is
  now green → built-up, and with Dynamic World dropped "built-up" can only come from a photo check.
- 2026-09-28 — **M4 measures against the RMP-2015 buffers, not the current ones.** Drains 50 m primary,
  25 m secondary, 15 m tertiary; lakes 30 m. Aditya's call. The September 2025 notification cut
  drains to 15/10/5 m, which is 1.5 pixels down to half a pixel and below what 10 m imagery and OSM
  outline error can resolve; the KTCDA lake bill's status is contested between sources. The old
  widths were in force for most of 2019-2026, so the claim is "land protected when the period
  began". State this framing in the published text. Step 0 is a pixel-count gate before any
  intersection is built.
- 2026-09-28 — **Lake-bed filling: found through the buffer, not measured directly.** Aditya's call.
  Encroachment on a lake bed usually comes with building in its ring and on its wetland margin
  (wetland pixels are kept in the masked table, and 2 of M2's top 3 losses are wetland), so a buffer
  hit flags the lake and the photo check then looks at the bed. Two limits to state: open water
  filled and built on is not a greenness loss at all (water and roofs both read low), so only the
  photos can see it; and a tank erased before OSM mapped it has no outline and no buffer.
- 2026-09-28 — **Step 0, geometry half: `measure_rings.py` → `results/m4_ring_pixels.csv`.** Each lake's
  30 m ring counted on the Sentinel-2 grid (EPSG:32643, pixel centres) in three 10 m bands; the
  0-10 m band is the shoreline and is dropped, so "clean" is the outer 20 m. Large lakes give 2.0
  clean pixels per 10 m of shore, as the geometry says they should. A lake is one OSM element plus
  anything touching it: Bellandur and Varthur are each one relation in several disjoint pieces, and
  counting pieces as lakes had split them. 3,486 lakes, 2,532 of them under 0.1 ha.
- 2026-09-28 — **What a lake is: OSM, 1 ha or more (590 lakes). Aditya's call, for simplicity.**
  Evidence: two random samples of 15 photo-checked (`sample_lakes.py`, `results/m4_lake_verdicts.csv`):
  1-5 ha is 12 tanks, 2 unclear, 1 drain; 0.1-1 ha is no bunded tank at all (4 not lakes, 3 ponds,
  3 farm or campus ponds, 2 quarry pits, 2 gone, 1 unclear). Against the official inventories
  (`compare_lake_inventories.py`, `data/inventories/`, `results/m4_inventory_compare.csv`): 92% of
  OSM lakes of 1 ha or more touch a KSRSAC tank, 88% an ATREE lake; OSM finds 77% of KSRSAC's 770
  tanks in the study area, 94-100% from 5 ha up. Rejected: KSRSAC (no licence or date stated) and
  ATREE (CC-BY, 2022), which would have added the ~175 tanks OSM has no water for. Dry-season water
  share cannot define a lake: real tanks read 0% when dry or under weed. **Limits to state when
  publishing:** the ring starts at mapped water, not the legal tank edge (OSM outlines are a median
  0.79 of KSRSAC's), so the claim is "within 30 m of mapped water"; tanks OSM does not map as water,
  which are likely the dry and built-over ones, are not in the study; 3.3% of the study area
  (Bengaluru South district side) is outside both inventories, which matters only as a cross-check.
  The legal definition (KTCDA Act s.2(g): any tank in revenue records, water or not) is the reason
  an inventory would be more correct; the 1 ha cutoff may be replaced by whatever floor the
  readability test gives.
- 2026-09-28 — **KTCDA amendment status is contested between sources**: one search says the Governor
  did not sign it, another reports Karnataka Act 19 of 2026 notified 18 Feb 2026 with size-graded
  buffers (0-30 m, from the revenue boundary). It does not change the RMP-2015 decision. Verify
  before publishing any sentence about current law.
- 2026-09-28 — **Drains dropped from M4: lakes only.** Aditya's call. The one classified drain map
  (KSRSAC 2022 KML on OpenCity: 163 primary / 870 secondary / 5,806 tertiary lines, public domain)
  covers only the old BBMP area, and that is where the greenness ranking is blind: the least-green
  decile contributes 0 of M2's top 40 (the 09-21 limit). The fringe, where the losses are, has no
  classified drains, and classifying them ourselves is untested work. Also against it: drain
  channels sit inside their own buffers and would need cutting out, and KSRSAC and MOD Foundation
  disagree on class lengths (primary 329 vs 382 km). The KML stays listed as a source if this
  is ever reopened.
- 2026-09-28 — **Step 0 gate criteria, fixed before the Earth Engine numbers exist** (Claude's call,
  provisional; Aditya asked for no more check-ins). Run: `measure_ring_greenness.py` →
  `results/m4_ring_table.csv`, 590 lakes x 3 bands x 8 years. Values normalised by subtracting the
  city-wide yearly mean of the masked hex table, as in M2. `scatter` = standard deviation of a band's
  eight normalised values about its own straight-line fit.
  1. **Grid check.** Earth Engine's pixel count equals the local count in at least 99% of bands.
     Fail → stop, the grid is not the one counted.
  2. **Edge test.** If the median over lakes of scatter(10-20 m) / scatter(20-30 m) exceeds 1.25,
     the shore is leaking into the middle band and "clean" becomes the 20-30 m band alone.
  3. **Readability.** A lake is readable if M2's rank-40 loss (0.105) is at least 3x the noise of an
     endpoint change, taken as sqrt(2) x scatter of its clean band: scatter <= 0.0247. Known bias:
     a real sudden loss inflates scatter, so this under-counts the lakes it matters for; the gate
     is about the population, and any lake that fails it is still photo-checkable.
  Reverse by editing the constants in the gate notebook.
- 2026-09-28 — **Step 0 result (`measure_ring_greenness.py`, `notebooks/m4_ring_gate.ipynb`).**
  - **Grid check failed as written, and the failure was not the grid.** Exact counts matched in
    58.6% of bands, 90.4% within 1 px, mean gap -0.001 px. Earth Engine's own pixel centres for
    six mismatched bands equal the local centres exactly; every mismatch is within 0.064 m of a band
    edge, a tie decided by the EPSG:4326 round trip. The 99%-exact rule tested edge ties, not the
    grid; replaced by the pixel-centre check (Claude's call, logged openly rather than retuned).
  - **Edge test: no leak, clean is 10-30 m.** Median scatter ratio 10-20 / 20-30 = 1.15 (limit
    1.25); 0-10 / 20-30 = 1.51, so the test does separate the shoreline band.
  - **Readability: 209 of 590 lakes (35%).** Median ring scatter is about 0.03, above the 0.0247
    limit and above a hex's 0.016-0.031: a 20 m strip is noisier than 8,000 pixels. The share is
    flat with size (1-5 ha 33%, 10-40 ha 43%); lakes of 100 ha and up have the noisiest rings
    (median 0.076). Readability is a per-lake flag, not a milestone pass/fail.
  - **First look.** Only 2 readable lakes lose more than the rank-40 hex loss; 27 unreadable ones
    do, and the top of that list is Ramapura, Horamavu, Heelalige, Bellandur, Hoodi,
    Mallathahalli, Gunjur and Varthur — famous lakes, several known to be under rejuvenation. If
    the photo check confirms lake works dominate, M4's headline rests on the provisional M2
    lake-works call.
- 2026-09-28 — **The gains list, photo-checked (`notebooks/m2_gain_photo_check.ipynb` →
  `results/m2_gain_verdicts.csv`).** Same ranking as `m2_masked.ipynb` section 7, same method as the
  losses. Of the 40 biggest gains: **6 real gain** (plantation blocks at Jarakabandekaval ranks 3-4,
  a tree plantation at Chagalatti 9 and 24, plantation blocks at Kodagalahatti 15, a villa
  township's gardens 28), 13 lake margin (tanks refilled after 2021, weed and marsh spreading over
  the bed past a low-water OSM outline), 13 doubtful, 3 crop swing, 3 regrowth (grass on empty
  layouts and the airport's 2019 earthworks), 2 artefact (Hennagara, which OSM maps as a sliver;
  a Hesaraghatta sliver underwater in 2023). All 6 real gains are clean and hold with a 2020 start.
  **No gain is a lake restoration**, so the M7 counter-example is a plantation, not the
  Kaikondrahalli-style story the scope table imagined: Jarakabandekaval first (two adjacent clean
  hexes, largest gain either start year), Chagalatti second. The start year matters more for gains
  than losses: 13 of 40 leave the top 40 from 2020 (8 for losses).
- 2026-09-28 — **M4 step 1: the top 40 ring losses, photo-checked** (`render_ring_losses.py`,
  `notebooks/m4_ring_photo_check.ipynb` → `results/m4_ring_verdicts.csv`, `m4_ring_evidence.csv`).
  Selection fixed beforehand: the 40 most negative clean-ring changes, readable or not.
  - **8 real loss:** Guni Agrahara / Shivaram Karanth Layout (rank 9, layout road along the west
    ring), Dooravaninagar (10, road widening and rail works), Medi Agrahara (13, layout grid to the
    shore), Thubarahalli (19, towers on the east edge), Chittekarepalya (20, sheds on the south
    edge; the only readable one), Bylakere (21, layout roads and plots), Yarandahalli (30),
    Mallapura, Nelamangala (40). 6 of 8 hold with a 2020 start; Yarandahalli and Mallapura do not.
  - **18 lake works lead the list:** Ramapura, Horamavu, Heelalige, Hoodi, Mallathahalli, Gunjur,
    Chikkabanavara and more — drained, bund rebuilt as a bare or paved walkway, bed desilted. The
    30 m ring is exactly where a rejuvenation puts its bund. Kept out of the real-loss list, as in
    M2 (provisional; same reversal).
  - **Water arriving does not explain the top**, unlike M2: only one ring passes 8% open water in
    any year (#14, a flooding quarry pit near Sadahalli). The per-pixel ring water check is in the
    verdicts CSV.
  - **3 outline artefacts:** Bellandur and Varthur, whose rings take in lake bed between OSM's
    separate pieces (a single 2019→2020 step; from 2020 they rank 113 and 464), and a canalised
    drain mapped as a lake (#31). 9 doubtful.
  - **Readability does not pick the real losses:** 4 of the 40 are readable, 1 of the 8. A sudden
    loss inflates scatter, the bias logged with the criteria, so the flag is kept as information,
    not a filter.
  - **Spot-checked by the main session** against the photos: Ramapura, Heelalige, Guni Agrahara,
    Chittekarepalya — agree.
- 2026-09-28 — **M4 closed (Claude's call, provisional).** The done-when is met: a list of specific
  lakes where vegetation was lost within 30 m of mapped water, each photo-checked. The story beat for
  M7 is "8 lakes where land in the ring was built on or cleared", with the lake-works finding beside
  it; which of the two leads is Aditya's editorial call.
- 2026-09-28 — **Lake works are not loss: confirmed by Aditya.** Settles the provisional M2 call of
  09-27 and its M4 twin. Scope is loss of green cover, and loss inside protected zones; a bund,
  walkway or desilting by the lake's own custodian is neither. So M4's headline is the 8 real
  losses, and the 18 lake works are context at most.
- 2026-09-29 — **M6 spec agreed on a working mockup** (a private artifact built from real imagery and
  results over the north-west fringe; build files not in the repo). Aditya's calls: the page opens on
  photos only with the change hexes a click away, and **gains are out of the site entirely** — no
  gain pins, the hex layer colours loss only, and M7's counter-example beat is dropped (so the
  09-28 Jarakabandekaval pick is moot; the gains check stays as the record). Claude's calls,
  provisional: all 38 pins show at once (few enough not to crowd), and the card's crops are
  Sentinel-2 (coarse for a single shed, but the Esri photos cannot be published).
- 2026-09-29 — **Front page carries visuals only; method and assumptions get their own page.**
  Aditya's call. The mockup's captions, verdict chips, ranks and the 2020 check move off the front
  page into "How it was made", which also holds the full per-place table. Claude's call,
  provisional: **dots are places, not hexes** — in the mockup window the 11 checked Shivaram
  Karanth Layout hexes are one dot ("11 of the city's 30 checked losses are here"), since eleven
  identical dots tell one story badly. M5 therefore needs a place grouping (neighbouring checked
  hexes merged, one plain sentence per place) alongside the hex table.
- 2026-09-29 — **The swipe shows two single clear days, not the season median** (Claude's call,
  provisional, after Aditya saw 2019 look softer and duller). Measured on a stable built-up patch
  (77.555-77.585E, 13.072-13.092N): single cloud-free days are equally sharp in both years (edge
  energy 4,100-4,650), but the 2019 Feb-Mar median is about 20% softer (3,223 vs 3,997) because it
  takes in hazy late-March days (19-25 and 30 Mar read bright and soft). Not misregistration: the
  2019 scenes are the reprocessed baseline 05.00. The pair **13 Feb 2019 / 11 Feb 2026** (both 0%
  cloud, same point in the season) matches on that patch (brightness 86.6 vs 84.5). Numbers keep
  using the median; the method page says so. **For M5:** the study area spans several Sentinel-2
  tiles, so each endpoint must be a same-day mosaic of one satellite pass, chosen by the same test.
- 2026-09-29 — **Mockup user-tested by an agent; fixes folded in.** Card crops are now fetched at
  native 10 m per place (the page-wide crop blown up 2x showed nothing); tapping after a drag hits
  what is under the finger; dots keep a 32 px touch target; the search says when nothing matches;
  the divider opens at 30% so the dots show 2026; a two-item key sits on the map; the loss ramp is
  yellow-to-dark-red for contrast on brown soil; the headline carries the number (30 stretches of
  farmland, 8 lakes); the method page opens with a plain three-line summary. The two Shivaram
  Karanth Layout clusters (9 and 2 hexes) are now two places, by the neighbouring-hexes rule.
- 2026-09-29 — **M5 closed: the static export** (Claude's calls throughout, provisional).
  - **The story is two fronts, and it is only visible city-wide.** Grouping the 30 checked hex losses
    by neighbours and adding the 8 lake-ring losses gives 22 places: 11 on the east (Varthur,
    Panathur, K Dommasandra out to Kolathuru and the Hoskote side), 5 in the north-west (the two
    Shivaram Karanth Layout blocks and Medi Agrahara, Guni Agrahara and Bylakere lakes), 6
    scattered. Aditya noted the one-window mockup showed no story; M6 opens at city scale for this.
  - **Photos: 13 Feb 2019 and 6 Feb 2026, one pass each.** The study area is two tiles (43PGQ,
    43PHQ) on relative orbit 19. 11 Feb 2026, the mockup's day, has 11.6% cloud on 43PHQ, so it
    cannot serve the whole city. On three stable built-up patches the chosen pair differs in
    brightness by -6.7, +3.6 and -2.4 (no one-way bias) with similar sharpness.
  - **Tiles fetched from Earth Engine's own map tiles** and packed with the `pmtiles` package, so no
    GDAL or tippecanoe is needed: 792 tiles a year, about 3 minutes each.
  - **Middle years are not exported.** The M6 spec no longer shows the eight-year line anywhere, so
    the "middle years as vector stats" half of the M5 plan has no reader. Reopen if M7 needs it.
  - **Place copy is editorial and lives in `site/places.csv`**, one plain sentence per place written
    from the photo-check notes, keyed by the top-ranked hex or the lake's OSM id. `export_vectors.py`
    fails if a place has no copy row or a copy row matches no place.
  - **Card photos need `filterBounds`:** a date-prefix filter alone makes Earth Engine mosaic every
    scene on Earth from that day and time out.
- 2026-09-29 — **M6 first build (`site/`), Claude's calls, provisional.** Two synced MapLibre maps
  (2019 below, 2026 on top clipped at the divider), so dots and hexes are drawn and clickable on
  both halves. Opens on the whole city with the two fronts labelled and a chip to fly to each.
  **Place labels from OpenFreeMap** (free, no key, OpenMapTiles schema): satellite imagery alone
  gives a public viewer no way to find where they are; a third-party dependency, noted in the
  method page's sources. **The surround outside the study area is dimmed** instead of showing
  black margins or unexplained photo. **Selecting a place flies to it and moves the divider onto
  it**, so both years are visible at once. **The loss hexes show only losses of 0.05 or more**
  (239 hexes): against the city average about half of all hexes lose *something* (1,464), which
  coloured half the city and buried the story; 0.05 is about twice a hex's year-to-year scatter
  (0.016-0.031, 09-21). **Deep links** `index.html#<place-id>` open a place directly. Local
  preview: `python site/serve.py` (range requests, no caching).
- 2026-09-29 — **First-visitor review of the M6 build**, in `REVIEW-first-visitor-2026-09-29.md`.
  Nothing changed yet. The main points are that the hero's "30 stretches" doesn't match the 14
  orange dots, the city-scale opening shows no visible change, there's no og:image or byline, and
  Shivaram Karanth is buried as the lede.

## Parked: the property/quality matrix

Not dead, just later. If revived, the key insights already worked out:

- The scatter plot will show a strong diagonal because price already reflects quality. **The residual is the finding**, not the plot: which localities are cheaper or dearer than their infrastructure justifies.
- Price prices the future; quality measures the present. Carry *change in quality over 5 years* as a third dimension, or metro-adjacent areas will look overpriced when they're just early.
- 6–8 metrics maximum. Check the correlation matrix first — if everything loads onto distance-from-centre, you've built an expensive centrality index.
- Prioritise metrics that vary independently of centrality: Cauvery connection vs. borewell, flooding history, commute time to *employment clusters* (Whitefield/ORR/E-City, not the geographic centre), canopy, air quality.
- Make the weights user-adjustable sliders. The weighting is inherently contestable; sliders turn that into a feature.
- Consider rent over sale price — rent tracks current livability, sale price embeds speculation. The rent-to-price ratio is itself a signal.
- **Milestone 3's canopy output feeds directly into this**, and it's the input nobody else has at this granularity.
