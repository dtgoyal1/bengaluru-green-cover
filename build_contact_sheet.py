"""Build results/imagery/index.html — every rendered frame beside its number.

Reads what render_sites.py and spot_check.py already wrote; fetches nothing.
"""

import csv
import json
from pathlib import Path

IMG = Path("results/imagery")
CSV = Path("results/m1_spot_check.csv")
NDVI_PALETTE = ["#8c510a", "#d8b365", "#f6e8c3", "#c7eae5", "#5ab4ac", "#01665e"]

CAPTIONS = {
	"varthur_built": (
		"Varthur — the area inside the yellow outline, <em>minus</em> the lake inside the red "
		"outline. The red region is excluded from every number on this page.",
	),
	"lalbagh": (
		"Lalbagh — the control. Every Varthur number in the project is quoted after subtracting "
		"this site, on the assumption that a mature botanical garden only moves with the weather.",
	),
}


def main() -> int:
	manifest = json.loads((IMG / "manifest.json").read_text())
	rows = list(csv.DictReader(CSV.open()))
	vals = {(r["site"], int(r["year"])): r for r in rows}

	by_site: dict[str, list[dict]] = {}
	for m in manifest:
		by_site.setdefault(m["site"], []).append(m)

	cards = []
	for site, entries in by_site.items():
		frames = []
		for m in sorted(entries, key=lambda e: e["year"]):
			y, n = m["year"], m["n"]
			rec = vals.get((site, y), {})
			ndvi = rec.get("ndvi") or ""
			mndwi = rec.get("mndwi") or ""
			ndvi_s = f"{float(ndvi):.3f}" if ndvi else "—"
			mndwi_s = f"{float(mndwi):.3f}" if mndwi else "—"
			thin = " thin" if 0 < n < 12 else ""
			if not m["rgb"]:
				frames.append(
					f'<figure class="frame empty"><div class="noimg">no usable imagery</div>'
					f'<figcaption><b>{y}</b><span class="n">0 scenes</span></figcaption></figure>'
				)
				continue
			mean_cloud = sum(m["clouds"]) / len(m["clouds"]) if m["clouds"] else 0
			frames.append(
				f'<figure class="frame{thin}">'
				f'<div class="pair">'
				f'<img loading="lazy" src="{m["rgb"]}" alt="{site} {y} true colour">'
				f'<img loading="lazy" src="{m["ndvi"]}" alt="{site} {y} greenness">'
				f"</div>"
				f"<figcaption><b>{y}</b>"
				f'<span class="v">green <b>{ndvi_s}</b></span>'
				f'<span class="v">wet <b>{mndwi_s}</b></span>'
				f'<span class="n">{n} scene{"s" if n != 1 else ""}, {mean_cloud:.0f}% cloud</span>'
				f"</figcaption></figure>"
			)
		cards.append(
			f'<section><h2>{site}</h2><p class="sub">{CAPTIONS[site][0]}</p>'
			f'<div class="grid">{"".join(frames)}</div></section>'
		)

	swatches = "".join(f'<i style="background:{c}"></i>' for c in NDVI_PALETTE)
	html = f"""<!doctype html>
<meta charset="utf-8"><title>Milestone 1 — imagery behind the numbers</title>
<style>
 :root {{ --bg:#fbfaf8; --fg:#1c1a17; --mut:#6a655e; --line:#e2ded7; --warn:#a8620d; }}
 @media (prefers-color-scheme:dark) {{
   :root {{ --bg:#15140f; --fg:#ece8e1; --mut:#9c968c; --line:#332f28; --warn:#e0a44d; }}
 }}
 body {{ margin:0; padding:28px 20px 60px; background:var(--bg); color:var(--fg);
        font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
 .wrap {{ max-width:1180px; margin:0 auto; }}
 h1 {{ font-size:26px; margin:0 0 6px; letter-spacing:-.02em; }}
 h2 {{ font-size:19px; margin:38px 0 4px; }}
 .sub, .lede {{ color:var(--mut); margin:0 0 14px; max-width:70ch; }}
 .legend {{ display:flex; gap:14px; align-items:center; flex-wrap:wrap;
            border:1px solid var(--line); border-radius:8px; padding:10px 14px; margin:16px 0 4px; }}
 .legend i {{ display:inline-block; width:26px; height:12px; }}
 .ramp {{ display:flex; }} .ramp i:first-child {{ border-radius:3px 0 0 3px; }}
 .ramp i:last-child {{ border-radius:0 3px 3px 0; }}
 .key {{ font-size:13px; color:var(--mut); }}
 .grid {{ display:grid; gap:18px; grid-template-columns:repeat(auto-fill,minmax(320px,1fr)); }}
 .frame {{ margin:0; border:1px solid var(--line); border-radius:9px; overflow:hidden; background:#0000000a; }}
 .frame.thin {{ border-color:var(--warn); }}
 .pair {{ display:grid; grid-template-columns:1fr 1fr; gap:1px; background:var(--line); }}
 .pair img {{ width:100%; display:block; aspect-ratio:700/460; object-fit:cover; }}
 figcaption {{ display:flex; gap:10px; align-items:baseline; flex-wrap:wrap; padding:8px 10px; font-size:13px; }}
 figcaption b {{ font-variant-numeric:tabular-nums; }}
 .v {{ color:var(--mut); }} .v b {{ color:var(--fg); }}
 .n {{ margin-left:auto; color:var(--mut); font-size:12px; }}
 .thin .n {{ color:var(--warn); }}
 .empty .noimg {{ aspect-ratio:1400/460; display:grid; place-items:center; color:var(--mut); font-size:13px; }}
</style>
<div class="wrap">
<h1>Milestone 1 — the imagery behind the numbers</h1>
<p class="lede">Left frame of each pair is true colour; right is greenness. Both are the
 dry-season (1 Feb – 31 Mar) median composite for that year — the exact same composite
 <code>spot_check.py</code> averaged to produce the numbers printed underneath. No cloud masking,
 matching the script. Years with fewer than 12 scenes are outlined in amber: the median cannot
 absorb haze at that sample size.</p>
<div class="legend">
 <span class="key">greenness</span>
 <span class="key">&minus;0.2</span><span class="ramp">{swatches}</span><span class="key">+0.8</span>
 <span class="key">brown = bare ground, buildings or open water &nbsp;·&nbsp; teal = dense vegetation</span>
</div>
{"".join(cards)}
</div>
"""
	(IMG / "index.html").write_text(html)
	print(f"wrote {IMG / 'index.html'}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
