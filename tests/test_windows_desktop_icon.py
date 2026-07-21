from __future__ import annotations

import hashlib
import struct
import zlib
from pathlib import Path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
REQUIRED_ICON_SIZES = (16, 24, 32, 48, 64, 128, 256)
SOURCE_PNG_SHA256 = "f626addd04f7e657c15971208bc92f067ef4dc15bc0b1b79609264093b6f4f2b"


def _decode_png(data: bytes) -> tuple[int, int, int, bytes]:
    assert data.startswith(PNG_SIGNATURE)
    position = len(PNG_SIGNATURE)
    width = height = color_type = bit_depth = 0
    compressed = bytearray()
    saw_iend = False
    while position < len(data):
        length = struct.unpack_from(">I", data, position)[0]
        position += 4
        chunk_type = data[position : position + 4]
        position += 4
        payload = data[position : position + length]
        position += length
        expected_crc = struct.unpack_from(">I", data, position)[0]
        position += 4
        assert zlib.crc32(chunk_type + payload) & 0xFFFFFFFF == expected_crc
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type = struct.unpack_from(">IIBB", payload)
        elif chunk_type == b"IDAT":
            compressed.extend(payload)
        elif chunk_type == b"IEND":
            saw_iend = True
            break
    assert saw_iend
    assert bit_depth == 8
    channels = {2: 3, 6: 4}[color_type]
    raw = zlib.decompress(bytes(compressed))
    stride = width * channels
    assert len(raw) == height * (stride + 1)
    assert all(raw[row * (stride + 1)] in range(5) for row in range(height))
    return width, height, channels, raw


def _ico_frames(data: bytes) -> dict[int, bytes]:
    reserved, image_type, count = struct.unpack_from("<HHH", data)
    assert reserved == 0
    assert image_type == 1
    frames: dict[int, bytes] = {}
    for index in range(count):
        offset = 6 + index * 16
        width_byte, height_byte, _colors, reserved_byte, planes, bits, size, start = (
            struct.unpack_from("<BBBBHHII", data, offset)
        )
        width = width_byte or 256
        height = height_byte or 256
        assert width == height
        assert reserved_byte == 0
        assert planes == 0
        assert bits == 32
        frames[width] = data[start : start + size]
    assert count == len(frames)
    return frames


def test_repository_png_is_exact_square_source_artwork() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    png = repo_root / "assets" / "branding" / "nwr_desktop_icon.png"
    data = png.read_bytes()
    assert hashlib.sha256(data).hexdigest() == SOURCE_PNG_SHA256
    width, height, channels, _raw = _decode_png(data)
    assert (width, height, channels) == (1254, 1254, 3)


def test_windows_ico_contains_decodable_required_frames() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    ico = repo_root / "assets" / "branding" / "nwr_desktop_icon.ico"
    frames = _ico_frames(ico.read_bytes())
    assert tuple(sorted(frames)) == REQUIRED_ICON_SIZES
    for size, payload in frames.items():
        width, height, channels, raw = _decode_png(payload)
        assert (width, height, channels) == (size, size, 4)
        assert len(set(raw)) >= 32
    for size in (16, 32):
        _width, _height, _channels, raw = _decode_png(frames[size])
        assert len(set(raw)) >= size


def test_installer_uses_only_repository_owned_primary_icon_path() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    installer = (repo_root / "scripts" / "Install Niners War Room Shortcut.ps1").read_text(
        encoding="utf-8"
    )
    uninstaller = (
        repo_root / "scripts" / "Uninstall Niners War Room Shortcut.ps1"
    ).read_text(encoding="utf-8")
    combined = installer + uninstaller
    assert "assets\\branding\\nwr_desktop_icon.ico" in combined
    assert "RefreshIcon=$true" in installer
    assert "RefreshIcon=$false" in installer
    assert "shell32.dll,13" in installer
    assert "Downloads" not in combined
    assert "ChatGPT Image" not in combined
    assert "desktop-logo-v1-20260721" not in combined
