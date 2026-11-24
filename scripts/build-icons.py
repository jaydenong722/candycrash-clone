"""
Regenerates the Huat Homes app icon (SVG source + every PNG size) and the
store-style screenshots used by the web app manifest.

It loads public/index.html in headless Chrome, pulls the game's own tile art
(pieceSVG / KEY_SVG), composes the icon, and renders it.

Usage (needs Python + Playwright with a Chromium/Chrome install):
    pip install playwright && playwright install chromium
    python scripts/build-icons.py
Set CHROME_PATH to use an existing Chrome binary instead of Playwright's.
"""
import asyncio, os, re, pathlib
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
ICONS = PUBLIC / "icons"
SHOTS = PUBLIC / "screenshots"


def inner(svg: str, prefix: str) -> str:
    """Strip the outer <svg> wrapper and namespace gradient ids."""
    body = re.sub(r"^<svg[^>]*>", "", svg.strip())
    body = re.sub(r"</svg>\s*$", "", body)
    for gid in set(re.findall(r'id="([^"]+)"', body)):
        body = body.replace(f'id="{gid}"', f'id="{prefix}{gid}"').replace(f"url(#{gid})", f"url(#{prefix}{gid})")
    return body


def tile(svg, prefix, x, y, size, rot):
    cx, cy = x + size / 2, y + size / 2
    return (f'<g transform="rotate({rot} {cx} {cy})"><svg x="{x}" y="{y}" width="{size}" height="{size}" '
            f'viewBox="0 0 100 100">{inner(svg, prefix)}</svg></g>')


def compose(pieces, key_svg, maskable=False, rounded=True):
    sky = []
    xs = [(-6, 70, 150), (60, 58, 112), (114, 64, 176), (172, 54, 128), (222, 70, 160),
          (288, 56, 120), (340, 66, 170), (402, 60, 118), (458, 64, 150)]
    for x, w, h in xs:
        sky.append(f'<rect x="{x}" y="{512 - h}" width="{w}" height="{h}" rx="4"/>')
    wins = []
    import random
    rnd = random.Random(7)
    for x, w, h in xs:
        for wy in range(512 - h + 14, 506, 18):
            for wx in range(x + 10, x + w - 12, 15):
                if rnd.random() < 0.35:
                    wins.append(f'<rect x="{wx}" y="{wy}" width="6" height="8" rx="1"/>')
    fg_scale = 0.85 if maskable else 1.0  # keep art inside the 80% maskable safe zone
    fg = (
        tile(pieces[1], "a", 44, 168, 190, -14)
        + tile(pieces[4], "b", 278, 168, 190, 14)
        + f'<circle cx="256" cy="246" r="128" fill="url(#glow)"/>'
        + tile(key_svg, "k", 136, 118, 240, 0)
        + '<g fill="#fff8d6">'
          '<path d="M98 112 l7 18 18 7 -18 7 -7 18 -7 -18 -18 -7 18 -7z"/>'
          '<path d="M420 96 l5 13 13 5 -13 5 -5 13 -5 -13 -13 -5 13 -5z"/>'
          '</g>'
    )
    clip = '<clipPath id="shape"><rect width="512" height="512" rx="112"/></clipPath>' if rounded else ''
    open_g = '<g clip-path="url(#shape)">' if rounded else '<g>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
<defs>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#2e2068"/><stop offset=".42" stop-color="#7a3d93"/>
    <stop offset=".75" stop-color="#e0668b"/><stop offset="1" stop-color="#ffb07a"/>
  </linearGradient>
  <radialGradient id="sun" cx=".5" cy=".5" r=".5">
    <stop offset="0" stop-color="#ffe9a8"/><stop offset=".55" stop-color="#ffb36b" stop-opacity=".85"/>
    <stop offset="1" stop-color="#ff8a64" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="glow" cx=".5" cy=".5" r=".5">
    <stop offset="0" stop-color="#fff3b0" stop-opacity=".9"/><stop offset="1" stop-color="#ffd23f" stop-opacity="0"/>
  </radialGradient>
  {clip}
</defs>
{open_g}
  <rect width="512" height="512" fill="url(#sky)"/>
  <circle cx="256" cy="372" r="190" fill="url(#sun)"/>
  <g fill="#2a1a58">{''.join(sky)}</g>
  <g fill="#ffd98a" opacity=".8">{''.join(wins)}</g>
  <g transform="translate(256 256) scale({fg_scale}) translate(-256 -256)">{fg}</g>
</g>
</svg>'''


async def main():
    exe = os.environ.get("CHROME_PATH") or ("/usr/bin/google-chrome" if os.path.exists("/usr/bin/google-chrome") else None)
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=exe, args=["--no-sandbox"]) if exe else await p.chromium.launch()
        page = await browser.new_page()
        await page.goto((PUBLIC / "index.html").as_uri())
        pieces = await page.evaluate("TYPES.map((_, i) => pieceSVG(i))")
        key_svg = await page.evaluate("KEY_SVG")

        variants = {
            "icon.svg": compose(pieces, key_svg, maskable=False, rounded=True),
            "icon-maskable.svg": compose(pieces, key_svg, maskable=True, rounded=False),
            "icon-square.svg": compose(pieces, key_svg, maskable=False, rounded=False),
        }
        for name, svg in variants.items():
            (ICONS / name).write_text(svg)

        renders = [  # (source svg, out png, size, transparent?)
            ("icon.svg", "icon-192.png", 192, True),
            ("icon.svg", "icon-512.png", 512, True),
            ("icon-maskable.svg", "maskable-192.png", 192, False),
            ("icon-maskable.svg", "maskable-512.png", 512, False),
            ("icon-square.svg", "apple-touch-icon.png", 180, False),
            ("icon.svg", "favicon-32.png", 32, True),
            ("icon.svg", "favicon-16.png", 16, True),
        ]
        for src, out, size, transparent in renders:
            pg = await browser.new_page(viewport={"width": size, "height": size}, device_scale_factor=1)
            svg = (ICONS / src).read_text().replace('width="512" height="512"', f'width="{size}" height="{size}"', 1)
            await pg.set_content(f'<html><body style="margin:0;background:transparent">{svg}</body></html>')
            await pg.screenshot(path=str(ICONS / out), omit_background=transparent,
                                clip={"x": 0, "y": 0, "width": size, "height": size})
            await pg.close()

        # manifest screenshots (narrow / phone)
        SHOTS.mkdir(exist_ok=True)
        pg = await browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
        await pg.goto((PUBLIC / "index.html").as_uri() + "?debug")
        await pg.wait_for_timeout(900)
        await pg.screenshot(path=str(SHOTS / "title.png"))
        await pg.evaluate("__hh.startLevel(6)")
        await pg.click("#mGo")
        await pg.wait_for_timeout(1200)
        await pg.screenshot(path=str(SHOTS / "gameplay.png"))
        await browser.close()

    # favicon.ico (16 + 32) via Pillow if present
    try:
        from PIL import Image
        Image.open(ICONS / "favicon-32.png").save(PUBLIC / "favicon.ico", sizes=[(16, 16), (32, 32)])
    except Exception as e:  # pragma: no cover
        print("favicon.ico skipped:", e)
    print("icons + screenshots written")


if __name__ == "__main__":
    asyncio.run(main())
