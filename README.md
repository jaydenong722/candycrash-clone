# Huat Homes 🏠🔑

A Singapore-property match-3 game inspired by Candy Crush, built as an installable **Progressive Web App**. Swipe to match shophouses, HDB flats, ECs, terraces, condos and bungalows. Lift the "cooling measures" and build your S$ portfolio.

- **Endless levels** with S$ portfolio targets, ice-block "cooling measures" and 1–3 star ratings
- **Zen mode** with no move limit
- **Special homes:** MRT Line (match 4), Reno Blast (L/T match), Golden Key (match 5), plus combos when you swap two specials
- **Boosters:** Demolish, En-bloc (shuffle) and +5 Lease
- Synthesised sound effects and music, vibration (Android), particles and screen shake
- **Installable and works offline.** Add it to your phone's home screen and it launches full-screen like a native app.

No frameworks, no build step and no dependencies: it's one HTML file plus a manifest and a service worker.

## Project layout

```
public/                  ← everything that gets deployed
  index.html             the whole game (HTML + CSS + JS)
  manifest.webmanifest   PWA manifest (name, icons, colours, screenshots)
  sw.js                  service worker: offline cache + font pre-caching
  favicon.ico
  icons/                 app icon: SVG source + PNGs (any / maskable / apple-touch)
  screenshots/           shown in Android's richer install dialog
scripts/build-icons.py   regenerates icons + screenshots from the game's own art
vercel.json              static hosting config + cache headers
```

## Run locally

Service workers need `http://localhost` or HTTPS (not `file://`):

```bash
npx serve public        # or: python3 -m http.server -d public 8080
```

Open http://localhost:3000. Add `?debug` to the URL to expose a `window.__hh` test hook.

## Deploy to Vercel

1. Import this repo at **vercel.com/new**.
2. Leave the Framework Preset as **Other**. No build command is needed; `vercel.json` already points the output directory at `public/`.
3. Deploy. Every push to `main` redeploys automatically.

Or from the CLI: `npx vercel --prod`.

## Install on your phone

- **Android (Chrome):** open the site, then tap **Install app** on the title screen (or ⋮ → *Install app*).
- **iPhone/iPad (Safari):** tap **Share** → **Add to Home Screen**. The title screen's *Install app* button shows these steps too.

## Updating the game

After changing files in `public/`, bump `VERSION` in `public/sw.js` (e.g. `huat-homes-v2`) so installed copies refresh their offline cache. The page itself is fetched network-first, so players get the latest version whenever they're online.

To regenerate the icons and screenshots (needs Python + Playwright):

```bash
pip install playwright && playwright install chromium
python scripts/build-icons.py
```
