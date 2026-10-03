"use strict";

const DATA = "data/";
const YEARS = [2019, 2026];
const DOT = { ground: "#ffffff", lake: "#56a8ef" };
const CHECKED = 40;
const LOSS_MIN = 0.05;
const LOSS_RAMP = ["interpolate", ["linear"], ["get", "loss"], LOSS_MIN, "#ffe08a", 0.08, "#f59e0b", 0.12, "#dc2626", 0.2, "#7f1d1d"];
const FRONTS = {
	"north-west": { title: "The north-west front", sub: "Shivaram Karanth Layout", story: true,
		text: (s) => `Shivaram Karanth Layout, on the city's north-west edge, is the biggest single place on this map: ${s.hexes} of the ${s.total} confirmed losses sit inside it, side by side. It is a Bangalore Development Authority layout of about 3,500 acres, and groundwork began in February 2023. By the next dry season, early 2024, the farmland and scrub had been scraped and a road grid laid across them. The grid runs up to the shores of Guni Agrahara and Medi Agrahara lakes, within 30 m of their water: the buffer that the same authority's master plan protects. A third lake nearby, Bylakere, was ringed by layout roads and plots between 2020 and 2023.` },
	east: { title: "The east front", sub: "Varthur to Hoskote", story: true,
		text: (s) => `The east is the opposite: no single project, but many. ${s.hexes} of the ${s.total} confirmed losses are spread over ${s.places} places from Varthur to Hoskote, and they came year after year, mostly from 2022 on. The single biggest loss on the map is here, at K Dommasandra and Kumbena Agrahara, where fields and a green wetland valley were scraped and built on from 2023. Around Varthur Lake, land beside the water and the green valley west of its wetland were cleared for building. Varthur flooded in September 2022, with boats on its streets, and officials blamed encroached storm-water drains and lost wetlands. Further out, the new Satellite Town Ring Road cut through farmland at Kolathuru in 2022, and a large warehouse followed in 2024. Two lakes, Thubarahalli and Dooravaninagar, had towers, a widened road and rail works built within 30 m of their water.` },
	elsewhere: { title: "Elsewhere", sub: "", text: () => "Single sites to the south and west." },
};
const FRONT_LABEL_MAX_ZOOM = 11.3;
const PLACE_MAX_ZOOM = { ground: 14.2, lake: 15 };

const protocol = new pmtiles.Protocol();
maplibregl.addProtocol("pmtiles", protocol.tile);

const $ = (id) => document.getElementById(id);
const stage = $("stage");
const card = $("card");
const state = { selected: null, hexes: true, cut: 50 };

function style(year) {
	const place = (id, classes, minzoom, size) => ({
		id, type: "symbol", source: "labels", "source-layer": "place", minzoom,
		filter: ["in", ["get", "class"], ["literal", classes]],
		layout: {
			"text-field": ["coalesce", ["get", "name:en"], ["get", "name"]],
			"text-font": ["Noto Sans Regular"],
			"text-size": size,
			"text-max-width": 8,
		},
		paint: { "text-color": "#ffffff", "text-halo-color": "rgba(0,0,0,0.78)", "text-halo-width": 1.4 },
	});
	return {
		version: 8,
		glyphs: "https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf",
		sources: {
			photo: { type: "raster", url: "pmtiles://" + new URL(`${DATA}${year}.pmtiles`, location.href).href, tileSize: 256 },
			labels: { type: "vector", url: "https://tiles.openfreemap.org/planet" },
		},
		layers: [
			{ id: "ground", type: "background", paint: { "background-color": "#0b0d0c" } },
			{ id: "photo", type: "raster", source: "photo" },
			place("labels-major", ["city", "town"], 8, 13),
			place("labels-minor", ["suburb", "village", "neighbourhood", "quarter"], 11.5, 12),
		],
	};
}

function addOverlays(map, data) {
	for (const [name, json] of Object.entries(data)) map.addSource(name, { type: "geojson", data: json, promoteId: name === "places" ? "id" : undefined });
	const below = "labels-major";
	map.addLayer({ id: "hex-fill", type: "fill", source: "hexes", filter: [">=", ["coalesce", ["get", "loss"], 0], LOSS_MIN],
		layout: { visibility: "visible" }, paint: { "fill-color": LOSS_RAMP, "fill-opacity": 0.5 } }, below);
	map.addLayer({ id: "hex-line", type: "line", source: "hexes", filter: [">=", ["coalesce", ["get", "loss"], 0], LOSS_MIN],
		layout: { visibility: "visible" }, paint: { "line-color": "rgba(255,255,255,0.25)", "line-width": 0.5 } }, below);
	map.addLayer({ id: "outside", type: "fill", source: "mask", paint: { "fill-color": "#0b0d0c", "fill-opacity": 0.72 } }, below);
	map.addLayer({ id: "boundary", type: "line", source: "boundary", filter: ["==", ["get", "role"], "study"],
		paint: { "line-color": "rgba(255,255,255,0.55)", "line-width": 1.2, "line-dasharray": [3, 2] } }, below);
	map.addLayer({ id: "sel-ring", type: "fill", source: "outlines", filter: ["==", ["get", "id"], ""],
		paint: { "fill-color": "rgba(86,168,239,0.45)", "fill-outline-color": "#b9e0ff" } });
	map.addLayer({ id: "sel-water", type: "line", source: "outlines", filter: ["==", ["get", "id"], ""],
		paint: { "line-color": "#b9e0ff", "line-width": 1.2, "line-dasharray": [2, 2] } });
	map.addLayer({ id: "sel-area", type: "line", source: "outlines", filter: ["==", ["get", "id"], ""],
		paint: { "line-color": "#ffffff", "line-width": 2, "line-dasharray": [3, 2] } });
	map.addLayer({ id: "places-halo", type: "circle", source: "places",
		paint: { "circle-color": "rgba(0,0,0,0.35)", "circle-radius": ["interpolate", ["linear"], ["zoom"], 9, 9, 14, 15] } });
	map.addLayer({ id: "places", type: "circle", source: "places",
		paint: {
			"circle-color": ["match", ["get", "kind"], "lake", DOT.lake, DOT.ground],
			"circle-radius": ["interpolate", ["linear"], ["zoom"], 9, 5.5, 14, 9],
			"circle-stroke-color": ["case", ["boolean", ["feature-state", "selected"], false], "#ffd35a", ["match", ["get", "kind"], "lake", "#ffffff", "#1c221f"]],
			"circle-stroke-width": ["case", ["boolean", ["feature-state", "selected"], false], 3.5, 1.8],
		} });
}

function extent(features) {
	const b = new maplibregl.LngLatBounds();
	const walk = (c) => (typeof c[0] === "number" ? b.extend(c) : c.forEach(walk));
	features.forEach((f) => walk(f.geometry.coordinates));
	return b;
}

async function main() {
	const files = ["hexes", "places", "outlines", "boundary"];
	const [hexes, places, outlines, boundary, details] = await Promise.all(
		[...files.map((f) => `${DATA}${f}.geojson`), `${DATA}details.json`].map((u) => fetch(u).then((r) => r.json())),
	);
	const byId = Object.fromEntries(places.features.map((f) => [f.properties.id, f]));
	const study = boundary.features.find((f) => f.properties.role === "study");
	const cityBounds = extent([study]);
	const grounds = details.filter((d) => d.kind === "ground").length;
	const lakesHit = details.filter((d) => d.kind === "lake").length;
	const frontOf = (h) => byId[h.properties.place].properties.front;
	const placed = hexes.features.filter((h) => h.properties.place);
	const stats = Object.fromEntries(Object.keys(FRONTS).map((k) => [k, {
		total: grounds,
		hexes: placed.filter((h) => frontOf(h) === k).length,
		places: places.features.filter((f) => f.properties.front === k && f.properties.kind === "ground").length,
	}]));
	const groundPlaces = places.features.filter((f) => f.properties.kind === "ground").length;
	$("stat").textContent = `We checked the ${CHECKED} biggest losses of green cover on Bengaluru's edge since 2019 by eye. ${grounds} were plainly real, in ${groundPlaces} places: farmland, scrub and wetland scraped for roads and buildings, ${stats["north-west"].hexes} of them in one new layout. ${lakesHit} lakes had roads or buildings pushed within 30 m of their water. These are only the biggest; the coloured hexagons show where the satellite saw more.`;

	const opts = {
		bounds: cityBounds, fitBoundsOptions: { padding: 24 }, minZoom: 8.5, maxZoom: 16,
		maxBounds: [[cityBounds.getWest() - 0.3, cityBounds.getSouth() - 0.3], [cityBounds.getEast() + 0.3, cityBounds.getNorth() + 0.3]],
		attributionControl: false, dragRotate: false, pitchWithRotate: false, touchPitch: false, cooperativeGestures: false,
	};
	const before = new maplibregl.Map({ container: "map-before", style: style(YEARS[0]), ...opts });
	const after = new maplibregl.Map({ container: "map-after", style: style(YEARS[1]), ...opts });
	const maps = [before, after];
	maps.forEach((m) => m.touchZoomRotate.disableRotation());
	after.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

	let syncing = false;
	for (const [a, b] of [[before, after], [after, before]]) {
		a.on("move", () => {
			if (syncing) return;
			syncing = true;
			b.jumpTo({ center: a.getCenter(), zoom: a.getZoom() });
			syncing = false;
		});
	}

	const ring = (g) => (g.type === "Polygon" ? g.coordinates[0] : g.coordinates.reduce((a, b) => (b[0].length > a[0].length ? b : a))[0]);
	const mask = { type: "Feature", properties: {}, geometry: { type: "Polygon", coordinates: [[[-180, -85], [180, -85], [180, 85], [-180, 85], [-180, -85]], ring(study.geometry)] } };
	const data = { hexes, places, outlines, boundary, mask };
	await Promise.all(maps.map((m) => new Promise((ok) => m.on("load", () => { addOverlays(m, data); ok(); }))));

	function setCut(v) {
		state.cut = Math.max(0, Math.min(100, v));
		stage.style.setProperty("--cut", state.cut + "%");
		$("knob").setAttribute("aria-valuenow", Math.round(state.cut));
	}
	const knob = $("knob");
	knob.addEventListener("pointerdown", (ev) => {
		knob.setPointerCapture(ev.pointerId);
		const moveTo = (e) => { const r = stage.getBoundingClientRect(); setCut(((e.clientX - r.left) / r.width) * 100); };
		const up = () => { knob.removeEventListener("pointermove", moveTo); knob.removeEventListener("pointerup", up); };
		knob.addEventListener("pointermove", moveTo);
		knob.addEventListener("pointerup", up);
	});
	knob.addEventListener("keydown", (ev) => {
		const step = { ArrowLeft: -3, ArrowRight: 3, Home: -100, End: 100 }[ev.key];
		if (step != null) { ev.preventDefault(); setCut(state.cut + step); }
	});
	setCut(50);

	const labels = Object.keys(FRONTS).filter((k) => k !== "elsewhere").map((k) => {
		const members = places.features.filter((f) => f.properties.front === k);
		const el = document.createElement("div");
		el.className = "front-label";
		el.innerHTML = `${FRONTS[k].title}<small>${FRONTS[k].sub} · ${members.length} places</small>`;
		el.style.position = "absolute";
		el.style.zIndex = 2;
		stage.appendChild(el);
		const b = extent(members);
		return { el, centre: [b.getCenter().lng, b.getNorth()], bounds: b };
	});
	function placeLabels() {
		const show = after.getZoom() < FRONT_LABEL_MAX_ZOOM;
		for (const l of labels) {
			const p = after.project(l.centre);
			l.el.hidden = !show;
			l.el.style.left = `${p.x}px`;
			l.el.style.top = `${p.y}px`;
			l.el.style.transform = "translate(-50%, calc(-100% - 14px))";
		}
	}
	after.on("move", placeLabels);
	placeLabels();

	function fly(bounds, maxZoom) {
		const narrow = stage.clientWidth < 700;
		after.fitBounds(bounds, { padding: narrow ? { top: 60, bottom: stage.clientHeight * 0.5, left: 30, right: 30 } : { top: 70, bottom: 70, left: 70, right: 400 }, maxZoom, duration: 1400 });
	}

	function highlight(id) {
		for (const m of maps) {
			if (state.selected) m.setFeatureState({ source: "places", id: state.selected }, { selected: false });
			if (id) m.setFeatureState({ source: "places", id }, { selected: true });
			const f = ["==", ["get", "id"], id || ""];
			m.setFilter("sel-ring", ["all", f, ["==", ["get", "role"], "ring"]]);
			m.setFilter("sel-water", ["all", f, ["==", ["get", "role"], "water"]]);
			m.setFilter("sel-area", ["all", f, ["==", ["get", "role"], "area"]]);
		}
		state.selected = id;
	}

	function select(id, { move = true } = {}) {
		const f = byId[id];
		if (!f) return;
		const p = f.properties;
		highlight(id);
		card.hidden = false;
		card.innerHTML = `<button class="x" type="button" aria-label="Close">×</button>
			<span class="eyebrow">${p.kind === "lake" ? "Built within 30 m of a lake" : "Green cover lost"}</span>
			<div class="name">${p.name}</div>
			<div class="pair">
				<figure><img src="${DATA}crops/${id}_2019.jpg" alt="${p.name}, 13 February 2019"><figcaption>13 Feb 2019</figcaption></figure>
				<figure><img src="${DATA}crops/${id}_2026.jpg" alt="${p.name}, 6 February 2026"><figcaption>6 Feb 2026</figcaption></figure>
			</div>
			<p>${p.text}</p>${p.fact ? `<p class="fact">${p.fact}</p>` : ""}
			<a href="method.html#checking">How we checked this</a>`;
		card.querySelector(".x").addEventListener("click", () => closeCard(true));
		history.replaceState(null, "", `#${id}`);
		$("reset").hidden = false;
		const bottom = stage.getBoundingClientRect().bottom;
		if (bottom > innerHeight) stage.scrollIntoView({ behavior: "smooth", block: "end" });
		if (move) {
			fly(extent(outlines.features.filter((o) => o.properties.id === id)), PLACE_MAX_ZOOM[p.kind]);
			after.once("moveend", () => setCut((after.project(f.geometry.coordinates).x / stage.clientWidth) * 100));
		}
	}

	function closeCard(refocus) {
		card.hidden = true;
		highlight(null);
		history.replaceState(null, "", location.pathname);
		if (refocus) knob.focus();
	}

	function hexCard(props) {
		highlight(null);
		const loss = props.loss;
		const say = loss >= 0.12 ? "A lot of green lost" : loss >= 0.08 ? "Clear green loss" : "Some green lost";
		card.hidden = false;
		card.innerHTML = `<button class="x" type="button" aria-label="Close">×</button>
			<span class="eyebrow">An area of about 0.76 km²</span>
			<div class="name">${say}</div>
			<p class="fact">Measured from the satellite, but not checked against the photos, so there is no story here yet.</p>`;
		card.querySelector(".x").addEventListener("click", () => closeCard(true));
	}

	for (const m of maps) {
		m.on("click", (e) => {
			const pad = 14;
			const hits = m.queryRenderedFeatures([[e.point.x - pad, e.point.y - pad], [e.point.x + pad, e.point.y + pad]], { layers: ["places"] });
			if (hits.length) {
				const dist = (f) => { const q = m.project(f.geometry.coordinates); return Math.hypot(q.x - e.point.x, q.y - e.point.y); };
				hits.sort((a, b) => dist(a) - dist(b));
				return select(hits[0].properties.id);
			}
			if (state.hexes) {
				const h = m.queryRenderedFeatures(e.point, { layers: ["hex-fill"] })[0];
				if (h) return h.properties.place ? select(h.properties.place) : hexCard(h.properties);
			}
		});
		m.on("mouseenter", "places", () => (m.getCanvas().style.cursor = "pointer"));
		m.on("mouseleave", "places", () => (m.getCanvas().style.cursor = ""));
	}

	$("hexbtn").addEventListener("click", () => {
		state.hexes = !state.hexes;
		$("hexbtn").setAttribute("aria-pressed", state.hexes);
		$("hexbtn").textContent = state.hexes ? "Hide where green was lost" : "Show where green was lost";
		$("hexkey").hidden = !state.hexes;
		for (const m of maps) for (const l of ["hex-fill", "hex-line"]) m.setLayoutProperty(l, "visibility", state.hexes ? "visible" : "none");
	});
	$("reset").addEventListener("click", () => {
		closeCard(false);
		$("reset").hidden = true;
		after.fitBounds(cityBounds, { padding: 24, duration: 1200 });
	});

	const fronts = $("fronts");
	for (const l of labels) {
		const k = Object.keys(FRONTS).find((key) => FRONTS[key].title === l.el.firstChild.textContent);
		const b = document.createElement("button");
		b.type = "button";
		b.className = "chip-btn";
		b.innerHTML = `<b>${FRONTS[k].title}</b> · ${FRONTS[k].sub}`;
		b.addEventListener("click", () => {
			closeCard(false);
			$("reset").hidden = false;
			stage.scrollIntoView({ behavior: "smooth", block: "center" });
			fly(l.bounds, 13);
		});
		fronts.appendChild(b);
	}

	const groups = $("groups");
	for (const [k, f] of Object.entries(FRONTS)) {
		const members = places.features.filter((p) => p.properties.front === k);
		if (!members.length) continue;
		const g = document.createElement("div");
		g.className = "group";
		g.innerHTML = `<h3>${f.title}${f.sub ? ` · ${f.sub}` : ""}</h3><p${f.story ? ' class="story"' : ""}>${f.text(stats[k])}</p><div class="strip"></div>`;
		for (const m of members) {
			const p = m.properties;
			const t = document.createElement("button");
			t.type = "button";
			t.className = "tile";
			t.innerHTML = `<div class="pair"><img src="${DATA}crops/${p.id}_2019.jpg" alt="" loading="lazy"><img src="${DATA}crops/${p.id}_2026.jpg" alt="" loading="lazy"></div>
				<h4><i class="dotkey ${p.kind}"></i>${p.name}</h4><p>${p.text}</p>`;
			t.addEventListener("click", () => { stage.scrollIntoView({ behavior: "smooth", block: "center" }); select(p.id); });
			g.querySelector(".strip").appendChild(t);
		}
		groups.appendChild(g);
	}

	$("search").addEventListener("submit", (ev) => {
		ev.preventDefault();
		const q = $("q").value.trim().toLowerCase();
		const msg = $("qmsg");
		if (!q) { msg.textContent = ""; return; }
		const hit = places.features.find((f) => f.properties.name.toLowerCase().includes(q));
		if (!hit) { msg.textContent = `No checked place called "${$("q").value.trim()}"`; return; }
		msg.textContent = "";
		stage.scrollIntoView({ behavior: "smooth", block: "center" });
		select(hit.properties.id);
	});

	const hash = location.hash.slice(1);
	if (byId[hash]) select(hash);
}

main().catch((err) => {
	console.error(err);
	stage.insertAdjacentHTML("beforeend", `<p style="position:absolute;inset:auto 14px 14px;color:#fff">The map could not load: ${err.message}</p>`);
});
