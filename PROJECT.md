# Bangalore Blue-Green Change (2019–2026)

**One-liner:** A static, interactive scrollytelling site showing exactly where Bangalore's tree canopy and water bodies gained or lost ground over ten years, using free Sentinel-2 imagery — measured per pixel across a fixed city boundary, so the output is a map of *where* it changed rather than a city-wide average.

**Audience:** LinkedIn / general public. Target 5–10 minutes of engagement.
**Not building:** a live tool, a backend, a scraper, or anything that needs maintenance after launch.

---

## How to resume a session

Paste this file into a new chat and say which milestone you're on. Update the **Status** and **Decision log** sections at the end of every working session — that's the whole trick to making a slow project survive gaps.

---

## Status

**Current milestone:** 2 — city-wide green. **M1 closed 2026-09-11** on a 2-of-3 gate
(flat ✓, loss ✓, gain ✗ — see below).
**Blocked on:** Nothing. All three of M1's open decisions are resolved.
**Next action:** Build the study boundary (GBA outer + ~10km ring) and lay the H3 res-8 grid over
it. That is M2's foundation and nothing can be measured before it exists.

**M2 is three layers, and only the third one downloads:**
  1. **Base** — greenness per pixel per year: 27M pixels x 8 years = 216M values. Stays server-side,
     never pulled (see the Java-background note on `.getInfo()`).
  2. **Change map** — the per-pixel difference, as a picture. 2019-vs-2026 endpoints are fine *for
     the image*; any quoted number must come from the 8-year slope instead, because endpoint choice
     swings the answer by more than the answer (see 2026-09-11).
  3. **Hex table** — H3 res 8, avg 0.737 km²: ~3,662 hexes x 8 years = ~29,295 rows. A small CSV.
     Rankings, locality search and charts are all built from this.

**Not in M2, and not in the project:** a city-wide aggregate score. Measured 2026-09-11 and it is
unreadable (t = 0.40, 95% range spans zero), and the scope table already cedes the aggregate story
to IISc. Do not reintroduce it.

Run `notebooks/m1_spot_check.ipynb` for the whole method end to end, and
`results/imagery/index.html` for the fastest eyeball check on any single number.
**Last worked on:** 2026-09-11

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
3. **NDVI can't distinguish trees from grass or crops.** Peri-urban agriculture masquerades as canopy. Dry-season imagery helps (grass browns, trees hold). Consider Google Dynamic World for actual land-cover classes if this proves noisy.
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

### 2 — City-wide green
Dry-season (Feb–Mar) median composite per year, 2019–2026, clipped to the boundary.
Per-pixel NDVI, then aggregate to H3 hexes.
- **Done when:** a hex-level NDVI time series covering the whole boundary, and a
  2019 vs 2026 per-pixel change layer
- **Watch:** water bodies are **not** masked — decided 2026-09-11, see the decision log. The mean is
  unaffected (0.92% of area, biasing *downward* by 0.002). The map is not: hyacinth reads as dense
  canopy and is invisible to MNDWI, so a cleared lake renders as canopy loss. Check the top-N
  changed hexes against imagery before any of them becomes a headline. If a per-year mask is ever
  reconsidered: it is disqualified, it makes things strictly worse.
- **Watch:** gotcha 8 forces the change layer to be *relative* — each hex against the city-wide
  median for that year, not against its own absolute value in 2019. An absolute per-hex delta will
  render a whole-city gain or loss that is only weather. Also gotcha 3 escalates here. At pixel level across the fringe, peri-urban
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
2019 vs 2026 draggable divider. Build this first — it's the centerpiece and everything else hangs off it.

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

- 2026-09-11 — **Decided: no lake masking. Skipped deliberately, not overlooked.** It moves the city
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

## Parked: the property/quality matrix

Not dead, just later. If revived, the key insights already worked out:

- The scatter plot will show a strong diagonal because price already reflects quality. **The residual is the finding**, not the plot: which localities are cheaper or dearer than their infrastructure justifies.
- Price prices the future; quality measures the present. Carry *change in quality over 5 years* as a third dimension, or metro-adjacent areas will look overpriced when they're just early.
- 6–8 metrics maximum. Check the correlation matrix first — if everything loads onto distance-from-centre, you've built an expensive centrality index.
- Prioritise metrics that vary independently of centrality: Cauvery connection vs. borewell, flooding history, commute time to *employment clusters* (Whitefield/ORR/E-City, not the geographic centre), canopy, air quality.
- Make the weights user-adjustable sliders. The weighting is inherently contestable; sliders turn that into a feature.
- Consider rent over sale price — rent tracks current livability, sale price embeds speculation. The rent-to-price ratio is itself a signal.
- **Milestone 3's canopy output feeds directly into this**, and it's the input nobody else has at this granularity.
