#!/usr/bin/env python3
"""Builds the animated SVGs used by README.md.

GitHub strips CSS/JS from READMEs, but an SVG loaded through <img> keeps its
own <style> and SMIL animations. Raster images referenced by such an SVG must be
inlined as data URIs, so the portrait is downscaled (macOS `sips`) and embedded.

    python3 scripts/build_svgs.py
"""
import base64
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "images" / "newasciiart.jpg"
OUT = ROOT / "assets"

MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
BG, BAR, FG, DIM = "#0b0f14", "#11171f", "#c9d6df", "#5c6f7c"
TEAL, PURPLE = "#8ab4c8", "#a58bd6"


def portrait_b64(width=880, quality=78):
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "p.jpg"
        subprocess.run(
            ["sips", "-Z", str(width), "-s", "format", "jpeg",
             "-s", "formatOptions", str(quality), str(SRC), "--out", str(out)],
            check=True, capture_output=True)
        return base64.b64encode(out.read_bytes()).decode()


def typed(text, x, y, begin, cps=22, size=13, fill=FG, cid="t"):
    """Text revealed char-by-char via a discretely-stepped clip rect.

    textLength pins the advance width so the clip steps land on glyph edges
    no matter which monospace font the viewer has.
    """
    cw = size * 0.6
    n = len(text)
    vals = ";".join(f"{i * cw:.1f}" for i in range(n + 1))
    dur = n / cps
    return f"""
  <clipPath id="{cid}"><rect x="{x}" y="{y - size}" height="{size * 1.5}" width="0">
    <animate attributeName="width" values="{vals}" calcMode="discrete"
             begin="{begin}s" dur="{dur:.2f}s" fill="freeze"/></rect></clipPath>
  <text x="{x}" y="{y}" textLength="{n * cw:.1f}" lengthAdjust="spacing"
        font-size="{size}" fill="{fill}" clip-path="url(#{cid})" xml:space="preserve">{text}</text>""", begin + dur


def prompt(x, y, size=13):
    """zsh-style prompt; returns (svg, width)."""
    cw = size * 0.6
    parts = [("~", TEAL), (" ❯ ", PURPLE)]
    out, cx = [], x
    for s, c in parts:
        out.append(f'<text x="{cx:.1f}" y="{y}" font-size="{size}" fill="{c}" '
                   f'textLength="{len(s) * cw:.1f}" xml:space="preserve">{s}</text>')
        cx += len(s) * cw
    return "\n  ".join(out), cx - x


def header():
    IW = 440
    IH = round(IW * 1352 / 2192)  # keep the source's 1.62:1 ratio
    pad = 18
    W = IW + 2 * pad
    title_h = 28
    ix, iy = pad, title_h + 40
    H = iy + IH + 46

    p1, pw = prompt(pad, title_h + 26)
    cmd, t_end = typed("chafa --symbols ascii ~/me.jpg", pad + pw, title_h + 26,
                       begin=0.6, cid="c1")

    # line-by-line "render" of the portrait, like output streaming in
    rows = 26
    reveal = ";".join(f"{IH * i / rows:.1f}" for i in range(rows + 1))
    r_begin, r_dur = t_end + 0.25, 1.6
    done = r_begin + r_dur

    p2, pw2 = prompt(pad, iy + IH + 29)
    cur_x = pad + pw2 + 2

    img = portrait_b64()

    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{MONO}">
<title>suryaanshs007 — ascii portrait</title>
<defs>
  <linearGradient id="border" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{W}" y2="{H}">
    <stop offset="0" stop-color="{TEAL}"/>
    <stop offset=".5" stop-color="{PURPLE}"/>
    <stop offset="1" stop-color="{TEAL}"/>
    <animateTransform attributeName="gradientTransform" type="rotate"
      from="0 {W / 2} {H / 2}" to="360 {W / 2} {H / 2}" dur="8s" repeatCount="indefinite"/>
  </linearGradient>
  <linearGradient id="scan" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#cfeaf5" stop-opacity="0"/>
    <stop offset=".5" stop-color="#cfeaf5" stop-opacity=".16"/>
    <stop offset="1" stop-color="#cfeaf5" stop-opacity="0"/>
  </linearGradient>
  <image id="me" x="{ix}" y="{iy}" width="{IW}" height="{IH}" preserveAspectRatio="xMidYMid slice"
         xlink:href="data:image/jpeg;base64,{img}"/>
  <clipPath id="frame"><rect x="{ix}" y="{iy}" width="{IW}" height="{IH}" rx="3"/></clipPath>
  <clipPath id="reveal"><rect x="{ix}" y="{iy}" width="{IW}" height="0">
    <animate attributeName="height" values="{reveal}" calcMode="discrete"
             begin="{r_begin:.2f}s" dur="{r_dur}s" fill="freeze"/></rect></clipPath>
  <clipPath id="g1"><rect x="{ix}" y="{iy + IH * .31:.0f}" width="{IW}" height="6"/></clipPath>
  <clipPath id="g2"><rect x="{ix}" y="{iy + IH * .58:.0f}" width="{IW}" height="4"/></clipPath>
  <clipPath id="g3"><rect x="{ix}" y="{iy + IH * .74:.0f}" width="{IW}" height="9"/></clipPath>
</defs>
<style>
  .scan {{ animation: scan 6s linear {done:.2f}s infinite; transform: translateY(-60px); }}
  @keyframes scan {{ to {{ transform: translateY({IH + 60}px); }} }}
  .gl {{ animation: gl 7s steps(1) {done + 1:.2f}s infinite; }}
  .gl.b {{ animation-duration: 9.5s; animation-delay: {done + 3.2:.2f}s; }}
  .gl.c {{ animation-duration: 11s; animation-delay: {done + 5.1:.2f}s; }}
  @keyframes gl {{
    0%, 90%, 100% {{ transform: translateX(0); }}
    91% {{ transform: translateX(-6px); }}
    92% {{ transform: translateX(4px); }}
    93% {{ transform: translateX(-2px); }}
  }}
  .cur {{ opacity: 0; animation: blink 1.05s steps(1) {done:.2f}s infinite; }}
  .after {{ opacity: 0; animation: show .01s {done:.2f}s forwards; }}
  @keyframes blink {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0; }} }}
  @keyframes show {{ to {{ opacity: 1; }} }}
  @media (prefers-reduced-motion: reduce) {{
    .scan, .gl {{ animation: none; }}
  }}
</style>

<rect x="1.5" y="1.5" width="{W - 3}" height="{H - 3}" rx="10" fill="{BG}"
      stroke="url(#border)" stroke-width="2"/>
<path d="M2.5 {title_h}H{W - 2.5}" stroke="#1c2530"/>
<text x="{pad}" y="{title_h / 2 + 4.5}" font-size="11" fill="{DIM}">foot</text>
<text x="{W / 2}" y="{title_h / 2 + 4.5}" font-size="11" fill="{DIM}" text-anchor="middle">suryaanshs007@arch: ~</text>
<text x="{W - pad}" y="{title_h / 2 + 4.5}" font-size="11" fill="{DIM}" text-anchor="end">[1]</text>

{p1}
{cmd}

<g clip-path="url(#reveal)">
  <use xlink:href="#me" clip-path="url(#frame)"/>
  <g clip-path="url(#frame)">
    <g clip-path="url(#g1)"><use class="gl" xlink:href="#me"/></g>
    <g clip-path="url(#g2)"><use class="gl b" xlink:href="#me"/></g>
    <g clip-path="url(#g3)"><use class="gl c" xlink:href="#me"/></g>
    <rect class="scan" x="{ix}" y="{iy}" width="{IW}" height="60" fill="url(#scan)"/>
  </g>
</g>

<g class="after">
  {p2}
  <rect class="cur" x="{cur_x:.1f}" y="{iy + IH + 18}" width="7.8" height="15" fill="{FG}"/>
</g>
</svg>
"""


def statusbar():
    """Waybar-style footer: workspace focus hops 1→5, braille spinner on the right."""
    W, H, size = 476, 28, 11
    cw = size * 0.6
    ws_x0, ws_gap = 14, 26
    hops = 5
    keyframes = []
    for i in range(hops):
        a, b = i * 100 / hops, (i + 1) * 100 / hops - 0.01
        keyframes.append(f"{a:.2f}%, {b:.2f}% {{ transform: translateX({i * ws_gap}px); }}")
    frames = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    spin = "".join(
        f'<text class="sp" style="animation-delay:{-0.08 * (len(frames) - i):.2f}s" '
        f'x="{W - 100}" y="{H / 2 + 4}" fill="{PURPLE}">{f}</text>'
        for i, f in enumerate(frames))
    ws = "".join(
        f'<text x="{ws_x0 + i * ws_gap + 9}" y="{H / 2 + 4}" text-anchor="middle" fill="{DIM}">{i + 1}</text>'
        for i in range(hops))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}"
     font-family="{MONO}" font-size="{size}">
<title>status bar</title>
<style>
  .hl {{ animation: hop 10s steps(1) infinite; }}
  @keyframes hop {{ {" ".join(keyframes)} }}
  .sp {{ opacity: 0; animation: sp .8s steps(1) infinite; }}
  @keyframes sp {{ 0% {{ opacity: 1; }} 10% {{ opacity: 0; }} }}
  @media (prefers-reduced-motion: reduce) {{ .hl, .sp {{ animation: none; }} .sp:first-of-type {{ opacity: 1; }} }}
</style>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="6" fill="{BAR}" stroke="#1c2530"/>
<rect class="hl" x="{ws_x0}" y="6" width="18" height="{H - 12}" rx="3" fill="{TEAL}" fill-opacity=".18" stroke="{TEAL}" stroke-opacity=".5"/>
{ws}
<text x="{W / 2}" y="{H / 2 + 4}" text-anchor="middle" fill="{FG}">suryaanshs007</text>
{spin}
<text x="{W - 87}" y="{H / 2 + 4}" fill="{DIM}" textLength="{len('building…') * cw:.1f}">building…</text>
</svg>
"""


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for name, fn in {"header.svg": header, "statusbar.svg": statusbar}.items():
        (OUT / name).write_text(fn(), encoding="utf-8")
        print(f"wrote assets/{name} ({(OUT / name).stat().st_size // 1024} KB)")
