import json
import struct
import subprocess
import sys
import zlib
from pathlib import Path

import pytest

from reference_color_sampler import (
    decode_png,
    sample_region_color,
    measure_box,
    PngDecodeError,
    RegionError,
)

THIS_DIR = Path(__file__).parent


# ---------------------------------------------------------------------------
# A standalone PNG encoder, used only by these tests to build fixtures. It is
# NOT the module under test's own code -- it exists so fixtures can be built
# without depending on reference_color_sampler.py being correct, which is the
# whole point of the test.
# ---------------------------------------------------------------------------

def _apply_filter(ftype: int, row: bytes, prev_row: bytes | None, bpp: int) -> bytes:
    out = bytearray(len(row))
    for x in range(len(row)):
        a = row[x - bpp] if x >= bpp else 0
        b = prev_row[x] if prev_row is not None else 0
        c = prev_row[x - bpp] if (prev_row is not None and x >= bpp) else 0
        v = row[x]
        if ftype == 0:
            out[x] = v
        elif ftype == 1:
            out[x] = (v - a) & 0xFF
        elif ftype == 2:
            out[x] = (v - b) & 0xFF
        elif ftype == 3:
            out[x] = (v - ((a + b) >> 1)) & 0xFF
        elif ftype == 4:
            p = a + b - c
            pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
            pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
            out[x] = (v - pr) & 0xFF
    return bytes(out)


def _chunk(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)


def encode_png(width, height, pixel_fn, color_type=6, filter_types=None):
    """pixel_fn(x, y) -> tuple of channel values matching color_type
    (RGBA for 6, RGB for 2). filter_types: per-row PNG filter type (0-4)."""
    channels = 4 if color_type == 6 else 3
    bpp = channels
    if filter_types is None:
        filter_types = [0] * height
    raw_rows = []
    for y in range(height):
        row = bytearray()
        for x in range(width):
            row.extend(pixel_fn(x, y))
        raw_rows.append(bytes(row))
    filtered = bytearray()
    prev = None
    for y in range(height):
        ftype = filter_types[y]
        filtered.append(ftype)
        filtered.extend(_apply_filter(ftype, raw_rows[y], prev, bpp))
        prev = raw_rows[y]
    ihdr = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    idat = zlib.compress(bytes(filtered), 9)
    return b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", idat) + _chunk(b"IEND", b"")


# A second, independently-written decoder used ONLY as a cross-check oracle in
# test_decode_matches_independent_oracle, so a bug shared between the fixture
# encoder above and reference_color_sampler.decode_png wouldn't be invisible.
def _oracle_decode_rgba(data: bytes):
    pos = 8
    width = height = None
    idat = bytearray()
    while pos + 8 <= len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        payload = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if kind == b"IHDR":
            width, height = struct.unpack(">II", payload[:8])
        elif kind == b"IDAT":
            idat.extend(payload)
        elif kind == b"IEND":
            break
    raw = zlib.decompress(bytes(idat))
    bpp = 4
    stride = width * bpp
    recon = bytearray(height * stride)
    pos = 0
    for y in range(height):
        ftype = raw[pos]
        pos += 1
        row = raw[pos:pos + stride]
        pos += stride
        out_row = bytearray(stride)
        for x in range(stride):
            a = out_row[x - bpp] if x >= bpp else 0
            b = recon[(y - 1) * stride + x] if y > 0 else 0
            c = recon[(y - 1) * stride + x - bpp] if (y > 0 and x >= bpp) else 0
            v = row[x]
            if ftype == 0:
                r = v
            elif ftype == 1:
                r = (v + a) & 0xFF
            elif ftype == 2:
                r = (v + b) & 0xFF
            elif ftype == 3:
                r = (v + (a + b) // 2) & 0xFF
            else:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                r = (v + pr) & 0xFF
            out_row[x] = r
        recon[y * stride:(y + 1) * stride] = out_row
    return width, height, [tuple(recon[i * 4:i * 4 + 4]) for i in range(width * height)]


def test_decode_matches_independent_oracle_across_all_five_filter_types():
    def pixel_fn(x, y):
        if x < 20:
            return (30, 120, 200, 255)
        if x % 5 == 0:
            return (255, 255, 255, 255)
        return (30, 120, 200, 255)

    data = encode_png(40, 40, pixel_fn, color_type=6, filter_types=[y % 5 for y in range(40)])
    image = decode_png(data)
    assert (image.width, image.height) == (40, 40)

    ow, oh, opixels = _oracle_decode_rgba(data)
    assert (ow, oh) == (40, 40)
    assert list(image.pixels) == opixels, "module decoder disagrees with the independent oracle"

    for y in range(40):
        for x in range(40):
            assert image.get(x, y) == pixel_fn(x, y), f"mismatch at ({x},{y})"


def test_decode_rgb_color_type_without_alpha():
    def pixel_fn(x, y):
        return (10 + x, 20 + y, 30)

    data = encode_png(16, 16, pixel_fn, color_type=2, filter_types=[1] * 16)
    image = decode_png(data)
    for y in range(16):
        for x in range(16):
            r, g, b, a = image.get(x, y)
            assert (r, g, b) == pixel_fn(x, y)
            assert a == 255, "RGB (no-alpha) PNGs must decode as fully opaque"


def test_median_resists_outliers_where_mean_would_not():
    """The core design claim read out of oil-ui's measure_reference.py: sampling
    the MEDIAN per channel, not the mean, so a region that is mostly one colour
    with a sprinkling of outlier pixels still reports the real colour. Proven by
    actually computing what the mean WOULD have given, not just asserting a
    median is "more robust" in the abstract."""
    base = (30, 120, 200, 255)
    outlier = (255, 255, 255, 255)
    pixels_in_region = []

    def pixel_fn(x, y):
        # 20x20 region, every 5th column an outlier -> 20% contamination.
        p = outlier if x % 5 == 0 else base
        pixels_in_region.append(p)
        return p

    data = encode_png(20, 20, pixel_fn, color_type=6, filter_types=[0] * 20)
    image = decode_png(data)

    result = sample_region_color(image, (0, 0, 20, 20))
    assert result["median_hex"] == "#1E78C8"  # exactly the base colour, 30,120,200 in hex

    # Sanity check the contamination is real: the mean over the same opaque
    # pixels is NOT the base colour -- confirming the outliers would have
    # skewed a mean-based sampler, so the median's correctness here is not
    # a coincidence of a contamination-free fixture.
    mean_r = sum(p[0] for p in pixels_in_region) / len(pixels_in_region)
    assert abs(mean_r - base[0]) > 15, "fixture must actually perturb the mean, or this test proves nothing"
    assert result["opaque_samples"] == 400
    assert result["excluded_nonopaque"] == 0


def test_inset_shrinks_sample_box_and_can_change_excluded_count():
    def pixel_fn(x, y):
        # outer ring semi-transparent (non-opaque), inner fully opaque base colour
        if x < 2 or y < 2 or x >= 18 or y >= 18:
            return (0, 0, 0, 0)
        return (50, 60, 70, 255)

    data = encode_png(20, 20, pixel_fn, color_type=6, filter_types=[0] * 20)
    image = decode_png(data)

    # Without inset, the 2px transparent ring is included in the sample box and
    # excluded from the opaque count.
    no_inset = sample_region_color(image, (0, 0, 20, 20), inset=0)
    assert no_inset["excluded_nonopaque"] > 0
    assert no_inset["median_hex"] == "#323C46"  # 50,60,70 in hex

    # With inset=2, the transparent ring is cropped out entirely before sampling.
    with_inset = sample_region_color(image, (0, 0, 20, 20), inset=2)
    assert with_inset["excluded_nonopaque"] == 0
    assert with_inset["sample_box"] == [2, 2, 16, 16]
    assert with_inset["median_hex"] == "#323C46"


def test_box_out_of_bounds_raises():
    data = encode_png(10, 10, lambda x, y: (0, 0, 0, 255), color_type=6)
    image = decode_png(data)
    with pytest.raises(RegionError):
        sample_region_color(image, (5, 5, 10, 10))


def test_fully_transparent_region_raises():
    data = encode_png(10, 10, lambda x, y: (0, 0, 0, 0), color_type=6)
    image = decode_png(data)
    with pytest.raises(RegionError, match="no opaque pixels"):
        sample_region_color(image, (0, 0, 10, 10))


def test_css_box_ratio_mapping_arithmetic():
    data = encode_png(100, 50, lambda x, y: (0, 0, 0, 255), color_type=6)
    image = decode_png(data)
    result = measure_box(image, (10, 10, 20, 10), css_viewport_width=1440)
    assert result["normalized_box"] == [0.1, 0.2, 0.2, 0.2]
    assert result["css_per_image_pixel"] == 14.4
    assert result["css_box"] == [144.0, 144.0, 288.0, 144.0]


def test_bad_signature_raises():
    with pytest.raises(PngDecodeError, match="signature"):
        decode_png(b"not a png")


def test_truncated_idat_raises():
    data = encode_png(10, 10, lambda x, y: (0, 0, 0, 255), color_type=6)
    # Corrupt the zlib stream by truncating near the end.
    truncated = data[:-20] + data[-4:]
    with pytest.raises(PngDecodeError):
        decode_png(truncated)


def test_cli_json_round_trip(tmp_path):
    data = encode_png(40, 40, lambda x, y: (30, 120, 200, 255), color_type=6)
    png_path = tmp_path / "ref.png"
    png_path.write_bytes(data)
    result = subprocess.run(
        [sys.executable, str(THIS_DIR / "reference_color_sampler.py"), str(png_path),
         "--color", "bg=0,0,20,20", "--box", "cta=20,20,10,10", "--css-width", "1440"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["regions"]["bg"]["median_hex"] == "#1E78C8"
    assert payload["regions"]["cta"]["css_box"] == [720.0, 720.0, 360.0, 360.0]


def test_cli_prints_clean_error_not_traceback_on_bad_box(tmp_path):
    data = encode_png(10, 10, lambda x, y: (0, 0, 0, 255), color_type=6)
    png_path = tmp_path / "ref.png"
    png_path.write_bytes(data)
    result = subprocess.run(
        [sys.executable, str(THIS_DIR / "reference_color_sampler.py"), str(png_path),
         "--color", "bad=5,5,10,10"],
        capture_output=True, text=True,
    )
    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    assert "out of bounds" in result.stderr
