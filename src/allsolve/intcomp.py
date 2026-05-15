# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

"""
Integer compression library for efficient storage of integer sequences.

Uses differential encoding combined with optional zstd compression or RLE.
"""

from enum import IntEnum
from typing import List, Optional
import zstandard as zstd

import allsolve.varint as varint


class Scheme(IntEnum):
    """Compression scheme used for encoding."""

    DIFF = 0  # Simple differential encoding
    DIFF_RLE = 1  # Differential + run-length encoding
    DIFF_ZSTD = 2  # Differential + zstd compression


VERSION = 0

# zstd file magic bytes
_ZSTD_MAGIC = bytes([0x28, 0xB5, 0x2F, 0xFD])


class _Header:
    """Internal header structure."""

    __slots__ = ("version", "scheme")

    def __init__(self, version: int, scheme: Scheme):
        self.version = version
        self.scheme = scheme


def encode(
    ints: List[int],
    zstd_compressor: Optional[zstd.ZstdCompressor] = None,
) -> bytes:
    """
    Encode a list of integers using differential compression.

    Automatically selects the best compression scheme:
    - DIFF for small arrays (≤4 elements)
    - DIFF_RLE for constant-difference sequences
    - DIFF_ZSTD for larger variable arrays

    Args:
        ints: List of integers to compress.
        zstd_compressor: Optional pre-created zstd compressor for reuse.
                        If None, a new one will be created when needed.

    Returns:
        Compressed bytes.
    """
    if len(ints) == 0:
        return b""

    # Calculate differences
    diffs = _calculate_diffs(ints)

    # Choose compression scheme
    if len(ints) <= 4:
        scheme = Scheme.DIFF
    elif _are_all_equal(diffs[1:]):
        scheme = Scheme.DIFF_RLE
    else:
        scheme = Scheme.DIFF_ZSTD

    header_byte = _encode_header(_Header(VERSION, scheme))

    if scheme == Scheme.DIFF:
        return _encode_diff(header_byte, diffs)
    elif scheme == Scheme.DIFF_RLE:
        return _encode_diff_rle(header_byte, diffs)
    else:
        if zstd_compressor is None:
            zstd_compressor = zstd.ZstdCompressor()
        return _encode_diff_zstd(header_byte, diffs, zstd_compressor)


def decode(
    encoded: bytes,
    zstd_decompressor: Optional[zstd.ZstdDecompressor] = None,
) -> List[int]:
    """
    Decode compressed integer data.

    Args:
        encoded: Compressed bytes from encode().
        zstd_decompressor: Optional pre-created zstd decompressor for reuse.
                          If None, a new one will be created when needed.

    Returns:
        List of decoded integers.
    """
    if len(encoded) == 0:
        return []

    header = _decode_header(encoded[0])
    data = encoded[1:]

    if header.scheme == Scheme.DIFF:
        return _decode_diff(data)
    elif header.scheme == Scheme.DIFF_RLE:
        return _decode_diff_rle(data)
    else:
        if zstd_decompressor is None:
            zstd_decompressor = zstd.ZstdDecompressor()
        return _decode_diff_zstd(data, zstd_decompressor)


def _calculate_diffs(ints: List[int]) -> List[int]:
    """Calculate differences between consecutive integers."""
    if len(ints) == 0:
        return []

    diffs = [ints[0]]
    for i in range(1, len(ints)):
        diffs.append(ints[i] - ints[i - 1])

    return diffs


def _are_all_equal(values: List[int]) -> bool:
    """Check if all values in the list are equal."""
    if len(values) == 0:
        return True

    first = values[0]
    for v in values[1:]:
        if v != first:
            return False
    return True


def _encode_header(header: _Header) -> int:
    """Encode header to a single byte."""
    return (header.scheme << 5) | header.version


def _decode_header(byte: int) -> _Header:
    """Decode header from a single byte."""
    return _Header(
        version=byte & 0x1F,
        scheme=Scheme(byte >> 5),
    )


def _encode_varint_list(ints: List[int]) -> bytes:
    """Encode a list of signed integers as varints."""
    return varint.encode_signed(ints)


def _encode_diff(header_byte: int, diffs: List[int]) -> bytes:
    """Encode using simple differential scheme."""
    return bytes([header_byte]) + varint.encode_signed(diffs)


def _encode_diff_rle(header_byte: int, diffs: List[int]) -> bytes:
    """Encode using differential + RLE scheme."""
    # Encode all parts using array functions and concatenate
    # This reduces individual function calls
    signed_parts = varint.encode_signed([diffs[0], diffs[1]])
    run_length_part = varint.encode_one(len(diffs) - 1)
    return bytes([header_byte]) + signed_parts + run_length_part


def _encode_diff_zstd(
    header_byte: int,
    diffs: List[int],
    compressor: zstd.ZstdCompressor,
) -> bytes:
    """Encode using differential + zstd scheme."""
    # Encode diffs as varints
    varint_data = _encode_varint_list(diffs)

    # Compress with zstd
    compressed = compressor.compress(varint_data)

    # Strip first 3 bytes of zstd magic number and replace 4th with our header
    # zstd magic is [0x28, 0xB5, 0x2F, 0xFD]
    result = bytearray(compressed[3:])
    result[0] = header_byte

    return bytes(result)


def _decode_diff(data: bytes) -> List[int]:
    """Decode differential scheme."""
    if len(data) == 0:
        return []

    # Decode all diffs at once
    diffs = varint.decode_signed(data)

    # Convert from differences to absolute values
    result = [diffs[0]]
    prev = diffs[0]
    for diff in diffs[1:]:
        prev = prev + diff
        result.append(prev)

    return result


def _decode_diff_rle(data: bytes) -> List[int]:
    """Decode differential + RLE scheme."""
    buffer = memoryview(data)

    # First value (signed)
    first_value, read = varint.decode_one_signed(buffer)
    buffer = buffer[read:]

    # Repeating difference (signed)
    repeating_value, read = varint.decode_one_signed(buffer)
    buffer = buffer[read:]

    # Run length (unsigned)
    run_length = varint.decode_one(buffer)[0]

    # Reconstruct the sequence
    result = [first_value]
    prev = first_value
    for _ in range(run_length):
        prev = prev + repeating_value
        result.append(prev)

    return result


def _decode_diff_zstd(
    data: bytes,
    decompressor: zstd.ZstdDecompressor,
) -> List[int]:
    """Decode differential + zstd scheme."""
    # Add zstd magic number back
    zstd_data = _ZSTD_MAGIC + data

    # Decompress using streaming API to handle frames without content size
    reader = decompressor.stream_reader(zstd_data)
    decompressed = reader.read()
    reader.close()

    # Decode as differential
    return _decode_diff(decompressed)
