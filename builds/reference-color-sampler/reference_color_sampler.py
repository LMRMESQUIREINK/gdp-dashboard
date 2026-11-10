"""A real, dependency-free (pure-stdlib) PNG color/layout sampler.

Built from reading oil-oil/oil-ui's scripts/measure_reference.py in full -- see
/notes/oil-ui-analysis.md -- but written independently rather than copied or executed:
this session's auto-mode classifier denies running an untrusted cloned repo's own code
("Code from External"), so the one checkable algorithmic claim worth verifying (a
pure-stdlib PNG decoder, used because this sandbox has no Pillow installed, confirmed
with `python3 -c "import PIL"` failing) was verified by careful line-by-line comparison
against a second, independently-written PNG decoder of this module's own, not by running
their script. That independent decoder passed its own oracle test (see
test_reference_color_sampler.py) before being trusted as the correctness reference.

The one design choice worth calling out, read directly from their code: color sampling
takes the per-channel MEDIAN across opaque pixels in a region, not the mean. A median
resists a sprinkling of outlier pixels (anti-aliased edges, a stray highlight, a logo's
white background bleeding into a sample box) that a mean would get pulled toward --
demonstrated directly in this module's own discrimination test, not just asserted.

Fills a real, concrete gap in this project's own tooling: /builds/ten-k-website-grader/
only greps CSS text for hex-literal colours (its own README states this as a limitation
-- it "deliberately not fixed by trimming" a page's real palette just to satisfy that
heuristic); design-rules.md's "derive the palette from one brand colour" rule has no
mechanism anywhere in this project for extracting a real colour from a reference image a
client supplies, only for choosing or stating one by hand. This module is that mechanism,
standing alone rather than wired into either (deliberate -- see README "what's deliberately
not built").
"""

from __future__ import annotations

import argparse
import json
import math
import struct
import sys
import zlib
from dataclasses import dataclass
from pathlib import Path
from statistics import median


class PngDecodeError(ValueError):
    pass


class RegionError(ValueError):
    pass


@dataclass(frozen=True)
class RGBAImage:
    width: int
    height: int
    pixels: tuple[tuple[int, int, int, int], ...]  # row-major, len == width*height

    def get(self, x: int, y: int) -> tuple[int, int, int, int]:
        return self.pixels[y * self.width + x]

    def crop(self, x: int, y: int, w: int, h: int) -> list[tuple[int, int, int, int]]:
        out = []
        for row in range(y, y + h):
            base = row * self.width
            out.extend(self.pixels[base + x: base + x + w])
        return out


_PALETTE_COLOR_TYPE = 3
_CHANNELS_BY_COLOR_TYPE = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}


def decode_png(data: bytes) -> RGBAImage:
    """Pure-stdlib 8-bit, non-interlaced PNG decoder. Supports color types 0
    (grayscale), 2 (RGB), 3 (palette + optional tRNS), 4 (grayscale+alpha), and 6
    (RGBA) -- the full set a real UI screenshot or reference image can be exported
    as. Unfilters every scanline per the PNG spec's own Sub/Up/Average/Paeth formulas."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise PngDecodeError("not a PNG file (missing signature)")
    pos = 8
    width = height = bit_depth = color_type = interlace = None
    idat = bytearray()
    palette: list[tuple[int, int, int]] = []
    trns = b""
    while pos + 8 <= len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        payload = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if kind == b"IHDR":
            width, height, bit_depth, color_type, _, _, interlace = struct.unpack(">IIBBBBB", payload)
        elif kind == b"PLTE":
            palette = [(payload[i], payload[i + 1], payload[i + 2]) for i in range(0, len(payload), 3)]
        elif kind == b"tRNS":
            trns = payload
        elif kind == b"IDAT":
            idat.extend(payload)
        elif kind == b"IEND":
            break
    if width is None or height is None:
        raise PngDecodeError("no IHDR chunk found")
    if bit_depth != 8:
        raise PngDecodeError(f"unsupported bit depth {bit_depth}; only 8-bit PNGs are supported")
    if interlace != 0:
        raise PngDecodeError("interlaced PNGs are not supported")
    if color_type not in _CHANNELS_BY_COLOR_TYPE:
        raise PngDecodeError(f"unsupported PNG color type {color_type}")
    if color_type == _PALETTE_COLOR_TYPE and not palette:
        raise PngDecodeError("palette color type with no PLTE chunk")

    channels = _CHANNELS_BY_COLOR_TYPE[color_type]
    stride = width * channels
    try:
        raw = zlib.decompress(bytes(idat))
    except zlib.error as exc:
        raise PngDecodeError(f"corrupt IDAT stream: {exc}") from exc
    if len(raw) != height * (stride + 1):
        raise PngDecodeError("IDAT stream is the wrong length for the declared dimensions")

    recon = bytearray(height * stride)
    in_pos = 0
    for y in range(height):
        ftype = raw[in_pos]
        in_pos += 1
        row_start = y * stride
        prev_start = (y - 1) * stride
        for x in range(stride):
            val = raw[in_pos]
            in_pos += 1
            a = recon[row_start + x - channels] if x >= channels else 0
            b = recon[prev_start + x] if y > 0 else 0
            c = recon[prev_start + x - channels] if (x >= channels and y > 0) else 0
            if ftype == 0:
                pass
            elif ftype == 1:
                val = (val + a) & 0xFF
            elif ftype == 2:
                val = (val + b) & 0xFF
            elif ftype == 3:
                val = (val + ((a + b) >> 1)) & 0xFF
            elif ftype == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                val = (val + pr) & 0xFF
            else:
                raise PngDecodeError(f"unknown PNG filter type {ftype} on row {y}")
            recon[row_start + x] = val

    pixels: list[tuple[int, int, int, int]] = []
    for i in range(width * height):
        off = i * channels
        if color_type == 6:
            pixels.append((recon[off], recon[off + 1], recon[off + 2], recon[off + 3]))
        elif color_type == 2:
            pixels.append((recon[off], recon[off + 1], recon[off + 2], 255))
        elif color_type == 4:
            g = recon[off]
            pixels.append((g, g, g, recon[off + 1]))
        elif color_type == 0:
            g = recon[off]
            pixels.append((g, g, g, 255))
        else:  # palette
            idx = recon[off]
            if idx >= len(palette):
                raise PngDecodeError(f"palette index {idx} out of range (palette has {len(palette)} entries)")
            r, g, b = palette[idx]
            alpha = trns[idx] if idx < len(trns) else 255
            pixels.append((r, g, b, alpha))
    return RGBAImage(width, height, tuple(pixels))


def _distribution(values: list[int]) -> dict:
    values = sorted(values)

    def quantile(p: float) -> float:
        pos = (len(values) - 1) * p
        lo, hi = math.floor(pos), math.ceil(pos)
        return round(values[lo] + (values[hi] - values[lo]) * (pos - lo), 3)

    return {"median": quantile(0.5), "p10": quantile(0.1), "p90": quantile(0.9)}


def _check_box(image: RGBAImage, x: int, y: int, w: int, h: int) -> None:
    if w <= 0 or h <= 0:
        raise RegionError(f"box width/height must be positive, got {w}x{h}")
    if x < 0 or y < 0 or x + w > image.width or y + h > image.height:
        raise RegionError(
            f"box [{x},{y},{w},{h}] is out of bounds for a {image.width}x{image.height} image"
        )


def sample_region_color(image: RGBAImage, box: tuple[int, int, int, int], inset: int = 0) -> dict:
    """Median per-channel colour across the OPAQUE pixels in box, after shrinking the
    box by `inset` on every side. Median, not mean, by design: see the module
    docstring and test_reference_color_sampler.py's discrimination test."""
    x, y, w, h = box
    _check_box(image, x, y, w, h)
    if inset < 0 or inset * 2 >= min(w, h):
        raise RegionError(f"inset {inset} leaves no sample area in a {w}x{h} box")
    sx, sy, sw, sh = x + inset, y + inset, w - inset * 2, h - inset * 2
    crop = image.crop(sx, sy, sw, sh)
    opaque = [p for p in crop if p[3] == 255]
    if not opaque:
        raise RegionError("no opaque pixels in the sample region (fully transparent box?)")
    channel_stats = [_distribution([p[c] for p in opaque]) for c in range(3)]
    rgb = [round(c["median"]) for c in channel_stats]
    return {
        "median_hex": "#" + "".join(f"{v:02X}" for v in rgb),
        "rgb_channels": channel_stats,
        "opaque_samples": len(opaque),
        "excluded_nonopaque": sw * sh - len(opaque),
        "sample_box": [sx, sy, sw, sh],
    }


def measure_box(image: RGBAImage, box: tuple[int, int, int, int], css_viewport_width: float | None = None) -> dict:
    """Normalized [0,1] box ratios, plus an optional css_box mapping when the
    reference image's assumed CSS viewport width is known."""
    x, y, w, h = box
    _check_box(image, x, y, w, h)
    result = {
        "box": [x, y, w, h],
        "normalized_box": [round(x / image.width, 6), round(y / image.height, 6),
                           round(w / image.width, 6), round(h / image.height, 6)],
    }
    if css_viewport_width is not None:
        if css_viewport_width <= 0:
            raise RegionError("css_viewport_width must be positive")
        factor = css_viewport_width / image.width
        result["css_per_image_pixel"] = factor
        result["css_box"] = [round(v * factor, 3) for v in box]
    return result


def _parse_spec(spec: str, label: str) -> tuple[str, tuple[int, int, int, int]]:
    if "=" not in spec:
        raise RegionError(f"--{label} must look like name=x,y,w,h, got {spec!r}")
    name, coords = spec.split("=", 1)
    parts = [p.strip() for p in coords.split(",")]
    if len(parts) != 4:
        raise RegionError(f"--{label} coords must be x,y,w,h (4 integers), got {coords!r}")
    try:
        box = tuple(int(p) for p in parts)
    except ValueError as exc:
        raise RegionError(f"--{label} coords must be integers: {exc}") from exc
    return name.strip(), box  # type: ignore[return-value]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="a PNG reference image")
    parser.add_argument("--color", action="append", default=[], metavar="NAME=X,Y,W,H")
    parser.add_argument("--box", action="append", default=[], metavar="NAME=X,Y,W,H")
    parser.add_argument("--inset", type=int, default=0, help="shrink --color sample boxes by this many pixels on each side")
    parser.add_argument("--css-width", type=float, default=None, dest="css_width")
    args = parser.parse_args(argv)

    try:
        image = decode_png(args.image.read_bytes())
        result: dict = {"source": str(args.image), "size": [image.width, image.height], "regions": {}}
        for spec in args.color:
            name, box = _parse_spec(spec, "color")
            result["regions"][name] = {"kind": "color", **sample_region_color(image, box, inset=args.inset)}
        for spec in args.box:
            name, box = _parse_spec(spec, "box")
            result["regions"][name] = {"kind": "box", **measure_box(image, box, args.css_width)}
        print(json.dumps(result, indent=2))
        return 0
    except (PngDecodeError, RegionError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
