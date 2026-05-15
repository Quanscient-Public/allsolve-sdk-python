# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

"""
Variable-length integer encoding (varint) implementation.

Uses 7-bit groups with continuation bits, and zig-zag encoding for signed integers.
"""

from typing import List, Tuple


def encode_one(value: int) -> bytes:
    """
    Encode a single unsigned integer using variable-length encoding.

    Uses 7 bits for data and 1 bit (MSB) as continuation flag for bytes 1-8.
    The 9th byte (if needed) uses all 8 bits.
    """
    if value < 0:
        raise ValueError(
            "encode_one() requires an unsigned integer, use encode_one_signed() for signed integers"
        )

    result = bytearray()

    # Process up to 8 bytes with 7 bits each (plus continuation bit)
    for _ in range(8):
        byte = value & 0x7F
        value >>= 7
        if value == 0:
            result.append(byte)
            return bytes(result)
        result.append(byte | 0x80)

    # 9th byte uses all 8 bits (no continuation bit needed)
    result.append(value & 0xFF)

    return bytes(result)


def encode_one_signed(value: int) -> bytes:
    """
    Encode a single signed integer using zig-zag encoding followed by varint encoding.

    Zig-zag encoding maps negative numbers to positive ones:
    0 -> 0, -1 -> 1, 1 -> 2, -2 -> 3, 2 -> 4, ...
    """
    # Zig-zag encode: (value << 1) ^ (value >> 63)
    # For Python's arbitrary precision ints, we need to handle the sign bit properly
    if value >= 0:
        zigzag = value << 1
    else:
        zigzag = ((-value - 1) << 1) | 1

    return encode_one(zigzag)


def encode(values: List[int]) -> bytes:
    """
    Encode multiple unsigned integers using variable-length encoding.
    """
    if len(values) == 0:
        return b""

    # Pre-allocate with a reasonable estimate (1-2 bytes per value on average)
    result = bytearray(len(values) * 2)
    pos = 0

    for value in values:
        if value < 0:
            raise ValueError(
                "encode() requires unsigned integers, use encode_signed() for signed integers"
            )

        # Inline encoding for performance
        # Process up to 8 bytes with 7 bits each (plus continuation bit)
        for _ in range(8):
            # Ensure we have space
            if pos >= len(result):
                result.extend(b"\x00" * len(result))

            byte = value & 0x7F
            value >>= 7
            if value == 0:
                result[pos] = byte
                pos += 1
                break
            result[pos] = byte | 0x80
            pos += 1
        else:
            # 9th byte uses all 8 bits (no continuation bit needed)
            if pos >= len(result):
                result.extend(b"\x00" * len(result))
            result[pos] = value & 0xFF
            pos += 1

    return bytes(result[:pos])


def encode_signed(values: List[int]) -> bytes:
    """
    Encode multiple signed integers using zig-zag encoding followed by varint encoding.

    Zig-zag encoding maps negative numbers to positive ones:
    0 -> 0, -1 -> 1, 1 -> 2, -2 -> 3, 2 -> 4, ...
    """
    if len(values) == 0:
        return b""

    # Pre-allocate with a reasonable estimate (1-2 bytes per value on average)
    result = bytearray(len(values) * 2)
    pos = 0

    for value in values:
        # Inline zig-zag encode
        if value >= 0:
            zigzag = value << 1
        else:
            zigzag = ((-value - 1) << 1) | 1

        # Inline varint encoding for performance
        # Process up to 8 bytes with 7 bits each (plus continuation bit)
        for _ in range(8):
            # Ensure we have space
            if pos >= len(result):
                result.extend(b"\x00" * len(result))

            byte = zigzag & 0x7F
            zigzag >>= 7
            if zigzag == 0:
                result[pos] = byte
                pos += 1
                break
            result[pos] = byte | 0x80
            pos += 1
        else:
            # 9th byte uses all 8 bits (no continuation bit needed)
            if pos >= len(result):
                result.extend(b"\x00" * len(result))
            result[pos] = zigzag & 0xFF
            pos += 1

    return bytes(result[:pos])


def decode(buffer: bytes | bytearray | memoryview) -> List[int]:
    """
    Decode all variable-length encoded unsigned integers from the buffer.

    Returns a list of decoded values.
    Raises ValueError if the buffer is invalid.
    """
    result = []
    pos = 0
    buf_len = len(buffer)

    while pos < buf_len:
        value = 0
        shift = 0

        for i in range(9):
            if pos >= buf_len:
                raise ValueError("varint.decode: buffer too short")

            byte = buffer[pos]
            pos += 1

            if i < 8:
                value |= (byte & 0x7F) << shift
                shift += 7
            else:
                # 9th byte uses all 8 bits
                value |= byte << shift

            if (byte & 0x80) == 0:
                break

        result.append(value)

    return result


def decode_signed(buffer: bytes | bytearray | memoryview) -> List[int]:
    """
    Decode all zig-zag encoded signed integers from the buffer.

    Returns a list of decoded values.
    """
    result = []
    pos = 0
    buf_len = len(buffer)

    while pos < buf_len:
        value = 0
        shift = 0

        for i in range(9):
            if pos >= buf_len:
                raise ValueError("varint.decode_signed: buffer too short")

            byte = buffer[pos]
            pos += 1

            if i < 8:
                value |= (byte & 0x7F) << shift
                shift += 7
            else:
                # 9th byte uses all 8 bits
                value |= byte << shift

            if (byte & 0x80) == 0:
                break

        # Zig-zag decode
        if value & 1:
            result.append(-(value >> 1) - 1)
        else:
            result.append(value >> 1)

    return result


def decode_one(buffer: bytes | bytearray | memoryview) -> Tuple[int, int]:
    """
    Decode a single variable-length encoded unsigned integer from the buffer.

    Returns a tuple of (decoded_value, bytes_consumed).
    Raises ValueError if the buffer is invalid.
    """
    if len(buffer) == 0:
        raise ValueError("varint.decode_one: buffer is empty")

    value = 0
    shift = 0

    for i in range(min(9, len(buffer))):
        byte = buffer[i]
        if i < 8:
            value |= (byte & 0x7F) << shift
            shift += 7
        else:
            # 9th byte uses all 8 bits
            value |= byte << shift

        if (byte & 0x80) == 0:
            return value, i + 1

    # If we've read less than 9 bytes and the last one has continuation bit set
    if len(buffer) < 9:
        raise ValueError("varint.decode_one: buffer too short")

    return value, 9


def decode_one_signed(buffer: bytes | bytearray | memoryview) -> Tuple[int, int]:
    """
    Decode a single zig-zag encoded signed integer from the buffer.

    Returns a tuple of (decoded_value, bytes_consumed).
    """
    value, length = decode_one(buffer)

    # Zig-zag decode: (value >> 1) ^ (-(value & 1))
    if value & 1:
        return -(value >> 1) - 1, length
    else:
        return value >> 1, length
