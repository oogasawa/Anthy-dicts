#!/usr/bin/env python3
"""
Convert ManbyoDic (MANBYO_*.csv of NAIST, CC BY 4.0, https://sociocom.naist.jp/manbyou-dic/) to the SKK dictionary form,
so that skk2anthy.py can turn it into an Anthy private dictionary.

Usage: manbyo2skk.py MANBYO_20210602.csv [--levels SABC] > manbyo.skk
       skk2anthy.py manbyo.skk --encoding utf-8 > manbyo.anthy.txt

The CSV columns are: the form that appears (出現形), its reading (出現形よみ), the ICD10 code, the standard disease name,
the reliability level of the coding (S, A, B, C, D, E, F) and the frequency level. The converter keeps the rows whose
reliability level is in --levels, whose reading is kana only, and whose form has a kanji, and it writes
"reading /form/". The readings of the level S come from the standard disease name master; the other readings were given by a
tool and partly corrected by hand, so the dictionary is a help for the candidates, not a ground truth.
"""
import argparse
import csv
import re
import sys

KANA = re.compile(r"^[ぁ-ゖァ-ヺー]+$")
KANJI = re.compile(r"[一-龥々]")


def to_hiragana(text):
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in text)


def entries(path, levels="SABC"):
    """Yield (reading, form) for the rows of a ManbyoDic CSV that the converter keeps."""
    seen = set()
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = csv.reader(f)
        next(rows)
        for row in rows:
            if len(row) < 5 or row[4] not in levels:
                continue
            form, reading = row[0].strip(), row[1].strip()
            if not form or not KANA.match(reading) or not KANJI.search(form) or "/" in form or "#" in form:
                continue
            reading = to_hiragana(reading)
            if (reading, form) in seen:
                continue
            seen.add((reading, form))
            yield reading, form


def main():
    p = argparse.ArgumentParser()
    p.add_argument("csv")
    p.add_argument("--levels", default="SABC", help="reliability levels to keep")
    a = p.parse_args()
    kept = 0
    for reading, form in entries(a.csv, a.levels):
        print(f"{reading} /{form}/")
        kept += 1
    print(f"{kept} entries", file=sys.stderr)


if __name__ == "__main__":
    main()
