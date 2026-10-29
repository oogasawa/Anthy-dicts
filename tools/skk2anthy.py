#!/usr/bin/env python3
"""
Convert an SKK dictionary (okuri-nasi entries) to the text form of an Anthy private dictionary.

Usage: skk2anthy.py SKK-JISYO.law [--encoding euc-jp] [--limit N] [--frequency 1] > words.txt
       cat words.txt | anthy-dic-tool --load   (this replaces the private dictionary of the user)

An SKK line is   reading /candidate1;annotation/candidate2/...   The converter keeps the entries whose reading is
hiragana only (the okuri-ari entries, whose reading ends with a letter, and the entries with numbers or Lisp
expressions are left out) and writes every candidate as a noun, with the settings that the Anthy documentation
gives for registering a noun (/usr/share/doc/anthy/dic-tool-usage.txt).
"""
import argparse
import re
import sys

HIRAGANA = re.compile(r"^[ぁ-ゖー]+$")
NOUN = ("品詞 = 名詞", "な接続 = y", "さ接続 = y", "する接続 = y", "語幹のみで文節 = y", "格助詞接続 = y")


def entries(path, encoding):
    with open(path, encoding=encoding, errors="replace") as f:
        for line in f:
            if line.startswith(";") or " /" not in line:
                continue
            reading, rest = line.rstrip("\n").split(" /", 1)
            if not HIRAGANA.match(reading):
                continue
            words = []
            for item in rest.split("/"):
                word = item.split(";", 1)[0].strip()
                if not word or word.startswith("(") or "#" in word or word in words:
                    continue
                words.append(word)
            if words:
                yield reading, words


def main():
    p = argparse.ArgumentParser()
    p.add_argument("skk")
    p.add_argument("--encoding", default="euc-jp")
    p.add_argument("--limit", type=int, default=0, help="stop after this many words (0: all)")
    p.add_argument("--frequency", type=int, default=1)
    a = p.parse_args()
    count = 0
    for reading, words in entries(a.skk, a.encoding):
        for word in words:
            print(f"{reading} {a.frequency} {word}")
            for setting in NOUN:
                print(setting)
            print()
            count += 1
            if a.limit and count >= a.limit:
                print(f"{count} words", file=sys.stderr)
                return
    print(f"{count} words", file=sys.stderr)


if __name__ == "__main__":
    main()
