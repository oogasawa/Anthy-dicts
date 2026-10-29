#!/usr/bin/env python3
"""
Take the nouns out of reading/text pairs cut into bunsetsu, with the number of times each was seen.

Input:  directories of *_pairs.tsv, each row  reading|with|bars <TAB> text|with|bars [<TAB> ...]
        (the pairs that kana-kanji-ime makes for its training: one bunsetsu per field between the bars)
Output: reading <TAB> word <TAB> count, the most frequent first

A bunsetsu is a word followed by its kana tail: the particles and the okurigana, written the same in the reading and
in the text (せいどが, 精度が). The word is the bunsetsu without the longest common tail of punctuation marks and hiragana before them. Only the words
that are nouns for sure are kept:
  - the word has no hiragana in it (精度, 30代前半, アウェー感; not 取り合い, whose part あい may be okurigana);
  - the word has a kanji in it (a word in katakana alone is typed as it is read);
  - the reading of the word is hiragana only (an Anthy dictionary has no reading with digits or letters);
  - the tail is particles only, and punctuation marks after them (が, には, の、); 書|く, 高|い and 上|がる are
    left out;
  - the word is seen with no tail, or with at least two different tails: the stem of a verb or an adjective is
    seen with one only, as 最|も and 既|に are, while a noun is seen with many (精度|が, 精度|の, 精度|を).
A word must be seen --min-count times with the same reading, which leaves out most of the readings that the
machine that made the pairs got wrong.
"""
import argparse
import collections
import os
import re
import sys
import zlib

KANJI = re.compile(r"[㐀-鿿豈-﫿々〆ヶ]")
HIRAGANA_CHAR = re.compile(r"[ぁ-ゖー]")
READING = re.compile(r"^[ぁ-ゖー]+$")
PARTICLES = ("が", "の", "を", "に", "へ", "と", "で", "や", "も", "は", "から", "まで", "より", "など", "だけ", "ほど",
             "ばかり", "こそ", "さえ", "でも", "しか", "について", "として", "による", "における")
PUNCTUATION = "、。，．,.！？!?」』）)・：:；;"
PARTICLE_RUN = re.compile("^(?:" + "|".join(sorted(PARTICLES, key=len, reverse=True)) + ")+$")


def split_of(chunk_name):
    """The split of kana-kanji-ime's build_dataset_g.py, so that the test chunks can be kept out."""
    bucket = zlib.crc32(chunk_name.encode("utf-8")) % 100
    return "valid" if bucket < 1 else "test" if bucket < 2 else "train"


def word_of(reading, text):
    """(reading of the word, the word, the tail), or None when the bunsetsu does not give a noun for sure."""
    common = 0
    while common < min(len(reading), len(text)) - 1 and reading[-1 - common] == text[-1 - common] \
            and text[-1 - common] in PUNCTUATION:
        common += 1
    while common < min(len(reading), len(text)) - 1 and reading[-1 - common] == text[-1 - common] \
            and HIRAGANA_CHAR.match(text[-1 - common]):
        common += 1
    word, word_reading, tail = text[:len(text) - common], reading[:len(reading) - common], text[len(text) - common:]
    if HIRAGANA_CHAR.search(word) or not KANJI.search(word) or not READING.match(word_reading):
        return None
    particles = tail.rstrip(PUNCTUATION)
    if particles and not PARTICLE_RUN.match(particles):
        return None
    return word_reading, word, particles


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pairs_dirs", nargs="+")
    parser.add_argument("--min-count", type=int, default=3)
    parser.add_argument("--all-splits", action="store_true",
                        help="also read the chunks that kana-kanji-ime keeps for validation and test")
    args = parser.parse_args()
    counts = collections.Counter()
    tails = collections.defaultdict(set)
    for pairs_dir in args.pairs_dirs:
        for name in sorted(os.listdir(pairs_dir)):
            if not name.endswith("_pairs.tsv") or (not args.all_splits and split_of(name) != "train"):
                continue
            with open(os.path.join(pairs_dir, name), encoding="utf-8") as f:
                for line in f:
                    columns = line.rstrip("\n").split("\t")
                    if len(columns) < 2:
                        continue
                    readings, texts = columns[0].strip().split("|"), columns[1].strip().split("|")
                    if len(readings) != len(texts):
                        continue
                    for reading, text in zip(readings, texts):
                        found = word_of(reading.strip(), text.strip())
                        if found:
                            counts[found[:2]] += 1
                            if len(tails[found[:2]]) < 2:
                                tails[found[:2]].add(found[2])
    for (reading, word), count in counts.most_common():
        if count < args.min_count:
            break
        if "" not in tails[(reading, word)] and len(tails[(reading, word)]) < 2:
            continue
        print(f"{reading}\t{word}\t{count}")


if __name__ == "__main__":
    main()
