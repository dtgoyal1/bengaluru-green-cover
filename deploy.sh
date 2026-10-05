#!/bin/sh
# Publish site/ to https://bengaluru-green-cover.pages.dev (Cloudflare Pages).
# Needs Node 22+ and a one-time `npx wrangler login`. Run from the repo root.
set -e
rm -rf out/deploy
mkdir -p out/deploy
rsync -a --exclude serve.py --exclude places.csv --exclude .DS_Store --exclude '*.pmtiles' site/ out/deploy/
npx --yes wrangler@latest pages deploy out/deploy --project-name bengaluru-green-cover --branch main --commit-dirty=true
