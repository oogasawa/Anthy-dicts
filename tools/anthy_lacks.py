#!/usr/bin/env python3
"""
Keep the words that Anthy does not offer for their reading.

Input:  reading <TAB> word [<TAB> ...] on stdin (what pairs2words.py writes)
Output: the input lines whose word is not among Anthy's candidates for the reading taken as one bunsetsu

Anthy is called through libanthy with the dictionaries of $HOME, as the input method would use them; run it with
HOME set to a copy of ~/.anthy to keep the dictionaries of the user out of reach.
"""
import ctypes
import sys

lib = ctypes.CDLL("libanthy.so.1")
lib.anthy_create_context.restype = ctypes.c_void_p
lib.anthy_context_set_encoding.argtypes = [ctypes.c_void_p, ctypes.c_int]
lib.anthy_set_string.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
lib.anthy_get_stat.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
lib.anthy_get_segment_stat.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
lib.anthy_get_segment.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
lib.anthy_resize_segment.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
UTF8 = 2


class ConvStat(ctypes.Structure):
    _fields_ = [("nr_segment", ctypes.c_int)]


class SegmentStat(ctypes.Structure):
    _fields_ = [("nr_candidate", ctypes.c_int), ("seg_len", ctypes.c_int)]


def candidates(context, reading):
    """The candidates of the reading taken as one bunsetsu."""
    lib.anthy_set_string(context, reading.encode("utf-8"))
    for _ in range(len(reading)):
        stat, segment = ConvStat(), SegmentStat()
        lib.anthy_get_stat(context, ctypes.byref(stat))
        lib.anthy_get_segment_stat(context, 0, ctypes.byref(segment))
        if stat.nr_segment <= 1 or segment.seg_len >= len(reading):
            break
        lib.anthy_resize_segment(context, 0, 1)
    segment = SegmentStat()
    lib.anthy_get_segment_stat(context, 0, ctypes.byref(segment))
    buffer = ctypes.create_string_buffer(4096)
    found = set()
    for i in range(segment.nr_candidate):
        if lib.anthy_get_segment(context, 0, i, buffer, 4096) > 0:
            found.add(buffer.value.decode("utf-8", "replace"))
    return found


def main():
    if lib.anthy_init() != 0:
        sys.exit("anthy_init failed")
    context = lib.anthy_create_context()
    lib.anthy_context_set_encoding(context, UTF8)
    for line in sys.stdin:
        columns = line.rstrip("\n").split("\t")
        if len(columns) >= 2 and columns[1] not in candidates(context, columns[0]):
            sys.stdout.write(line)


if __name__ == "__main__":
    main()
