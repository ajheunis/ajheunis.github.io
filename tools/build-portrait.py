"""Build the hero portrait used on the home page.

Source is a cut-out headshot with a hand-cleaned alpha channel, kept in this
directory rather than images/ because it is a build input and is never served.
This script does not key anything: it takes that matte as given and only does
the design treatment.

  1. tone to the brand palette - luminance from the photograph, hue and
     saturation from --accent, which is what `mix-blend-mode: color` does;
  2. lift the black point, so the near-black suit still reads as a silhouette
     against a near-black page instead of vanishing into it;
  3. dissolve the lower edge, so the figure emerges from the page rather than
     ending on the cut line where the source frame crops the torso;
  4. pad, then resize in premultiplied space so the transparent region cannot
     bleed a halo into the silhouette on downscale.

Run from the repo root:  python tools/build-portrait.py
"""

import colorsys
import os

import numpy as np
from PIL import Image

SRC = "tools/adam-heunis-profile-photo_no-bg.png"
OUT_STEM = "images/adam-heunis-portrait"

ACCENT = (0xC6, 0xA1, 0x5B)   # --accent
TONE_STRENGTH = 0.34          # how far toward the accent hue to carry it
CONTRAST = 1.06
BLACK_LIFT = 0.13             # keeps the black suit visible on a black page

# The source frame crops the torso at the bottom edge and clips the arm at the
# left below y=71%, so the fade has to start above that to hide both cuts.
DISSOLVE_START, DISSOLVE_END = 0.58, 0.93   # fraction of source height

PAD_TOP, PAD_SIDE, PAD_BOTTOM = 0.04, 0.03, 0.0

WIDTHS = (512, 640, 960)


def smoothstep(x, lo, hi):
    t = np.clip((x - lo) / (hi - lo), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def toned(rgb):
    """Grey the photograph, then carry it toward the accent hue."""
    lum = rgb @ np.array([0.2126, 0.7152, 0.0722]) / 255.0
    lum = np.clip((lum - 0.5) * CONTRAST + 0.5, 0.0, 1.0)
    lum = BLACK_LIFT + lum * (1.0 - BLACK_LIFT)

    h, _, s = colorsys.rgb_to_hls(*[c / 255.0 for c in ACCENT])
    ramp = np.array([colorsys.hls_to_rgb(h, v, s) for v in np.linspace(0, 1, 256)])
    tinted = ramp[(lum * 255).astype(np.uint8)]

    grey = np.repeat(lum[:, :, None], 3, axis=2)
    return np.clip(grey * (1 - TONE_STRENGTH) + tinted * TONE_STRENGTH, 0, 1) * 255


def dissolve(alpha):
    y = np.arange(alpha.shape[0]) / alpha.shape[0]
    return alpha * (1.0 - smoothstep(y, DISSOLVE_START, DISSOLVE_END))[:, None]


def pad(rgb, alpha):
    h, w = alpha.shape
    top, bottom = int(h * PAD_TOP), int(h * PAD_BOTTOM)
    side = int(w * PAD_SIDE)
    rgb = np.pad(rgb, ((top, bottom), (side, side), (0, 0)), mode="edge")
    alpha = np.pad(alpha, ((top, bottom), (side, side)), mode="constant")
    return rgb, alpha


def resize_premultiplied(rgb, alpha, width):
    """Resize with alpha premultiplied, so transparent pixels carry no colour."""
    h, w = alpha.shape
    height = round(width * h / w)
    size = (width, height)

    pm = Image.fromarray((rgb * alpha[:, :, None]).astype(np.uint8), "RGB").resize(size, Image.LANCZOS)
    a = Image.fromarray((alpha * 255).astype(np.uint8), "L").resize(size, Image.LANCZOS)

    pm = np.asarray(pm).astype(float)
    an = np.asarray(a).astype(float) / 255.0
    out = np.divide(pm, an[:, :, None], out=np.zeros_like(pm), where=an[:, :, None] > 0.004)
    return Image.fromarray(
        np.dstack([np.clip(out, 0, 255), an * 255]).astype(np.uint8), "RGBA"
    )


def main():
    src = Image.open(SRC).convert("RGBA")
    arr = np.asarray(src).astype(float)
    rgb, alpha = arr[:, :, :3], arr[:, :, 3] / 255.0

    rgb = toned(rgb)
    alpha = dissolve(alpha)
    rgb, alpha = pad(rgb, alpha)

    h, w = alpha.shape
    print(f"source {src.size} -> canvas {(w, h)}  (aspect {w / h:.4f})")
    for width in WIDTHS:
        out = resize_premultiplied(rgb, alpha, width)
        path = f"{OUT_STEM}-{width}.webp"
        out.save(path, "WEBP", quality=88, method=6)
        print(f"  {path}  {out.size}  {os.path.getsize(path):,} bytes")


if __name__ == "__main__":
    main()
