# First-visitor review of the M6 site, 2026-09-29

Claude looked at `site/` (served locally at http://localhost:8765) as someone seeing the project
for the first time, on desktop (1440 px) and mobile (390 px). Nothing below has been acted on yet.
Each item needs Aditya's call, and some of them run into decisions already agreed in PROJECT.md;
those are marked.

## Verdict

| Lens | Verdict | Why |
|---|---|---|
| Design | Strong, with small bugs | Dark editorial look, good typefaces, and the swipe works well once zoomed into a place (Panathur/Varthur looks great). |
| Message | Clear but undercut | "30 stretches… 8 lakes" is plain English, but the visitor counts 14 orange dots, not 30. |
| Impact | Medium | No size figure (km² lost) and no "why it matters", so it ends on "OK, and?" |
| Maturity | Grown-up, not childish | "What this cannot see" is rare even in professional work and earns trust. |
| Story | There is one, and it's buried | Shivaram Karanth Layout, see below. |

## Findings, most important first

1. **The headline number doesn't match the map.** The hero says "30 stretches", which counts
   hexes (M2's 30 quotable), but the map shows 14 ground places and 8 lakes (`site/places.csv`).
   Fix: say "30 patches, grouped into 14 places", or lead with the place count.
2. **It reads as a census, but it's a checked top 40.** "30 were scraped bare" sounds like the
   total for the city. Something like "the 30 biggest losses we could confirm" is more honest,
   and it hits harder because it's a minimum. There's no area figure: think about km² lost, or a
   share of the 2,175 km² study area.
3. **The first swipe probably shows nothing.** The map opens on the whole city, where one screen
   pixel is about 150 m and a hex is a few pixels, so the change is invisible. The payoff only
   comes after zooming in. *Runs into the M6 spec:* "opening at city scale so the two fronts
   show" and "hexes off at load". Options: open zoomed in on one place, turn the hexes on at
   load, or let M7's scrollytelling beats do the zooming.
4. **There's no link preview image.** `index.html` has no `og:image` or `og:title`, so a shared
   link shows a blank card. *Partly covered by M8* (small-multiples preview image, post a native
   video, put the link in the first comment), but the meta tags are still needed.
5. **Nobody made it.** The copy says "we", but there's no byline, date or reason for doing it.
   This is the one thing that makes it look like a side experiment.
6. **"Green ground" is an odd phrase.** People say "green cover" or "open land". Not wrong, but
   it makes the reader stop.

## Smaller design bugs

- **The attribution is clipped by the swipe.** It's attached to the `after` map, which is clipped
  at the divider, so it reads "apTiles Data from…" on desktop. On mobile the expanded box also
  covers the legend. Move it outside the clipped map, or onto the stage.
- **The front labels sit on top of their own dots**, and "· 5 places" wraps onto its own line
  (`.front-label` max-width 170 px).
- **Orange means two things.** The orange dots and the yellow-to-red hex ramp both mean "green
  lost", so a first-timer may read them as different measures.
- **Not confirmed:** in one headless drag test the two maps looked out of sync. Probably a
  problem with the test itself, since `app.js` syncs both ways. Drag on the left pane by hand to
  check.

## False alarms (don't re-investigate)

- **Black thumbnails under "Elsewhere" and on mobile:** the images use `loading="lazy"` and a
  full-page screenshot never scrolls to them.
- **Header repeated partway down the mobile full-page capture:** a glitch in how puppeteer
  captures full mobile pages.

## The underlying story

- There are two kinds of growth. The east (Varthur, Panathur, Hoskote) is scattered, piecemeal
  sprawl. The north-west is one planned layout, Shivaram Karanth Layout: the single biggest loss,
  with roads pushed up to three lakes. Right now that fact appears only inside one card.
- **To verify before using:** Claude believes Shivaram Karanth Layout is a BDA layout (from
  memory, unsourced). If that holds, the lede is that the authority that wrote the 30 m lake
  buffer is behind the biggest planned clearing, with its roads up to three lakes.
- **Stakes:** Varthur is where the 2022 floods hit hardest. One line on lake buffers and flooding
  would answer "why should I care". Don't claim the clearing caused the floods. The existing
  "within 30 m of mapped water" wording stays safe on the legal side.

## Open decisions for Aditya

- Should the page open at city scale (current spec) or zoomed in on one place, and should the
  hexes be on at load?
- Headline wording: hex count, place count, or "at least"?
- Should Shivaram Karanth / BDA be the lede, once sourced?
- Byline, and a one-line "why".
