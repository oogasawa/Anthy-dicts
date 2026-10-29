#!/usr/bin/env python3
"""
Keep the words whose reading can be made of the readings of their characters.

Input:  reading <TAB> word [<TAB> ...] on stdin
Output: the input lines whose reading is made of a reading of every character of the word, in order

The readings of a kanji are its on and kun readings and its name readings (nanori) in KANJIDIC2. A kun reading of a
verb is taken whole and in the form it has inside a noun (割|る gives わる and わり as in 割引), not as its stem
alone (組|む does not give く). A reading may change as it does
inside a word: the first kana of a kun or name reading after the first character can be voiced (人々 ひとびと,
雨傘 あまがさ), and an on reading after ん or っ can be voiced or get the p sound (三階 さんがい, 発表 はっぴょう);
the last つ, く, ち or き of a reading before another character can become っ (学校 がっこう) when the next
reading starts with a sound of the か, さ, た or ぱ rows. 々 repeats the
readings of the character before it, ヶ and ケ are read が, か or こ, and katakana is read as it is.
Readings that the machine that made the pairs got wrong are left out this way: 交流 こうりょう, 手間 てまえ,
個々 こここ, 自粛 じじゅく.
Usage: reading_check.py KANJIDIC2_XML_GZ < words.tsv > checked.tsv
"""
import gzip
import re
import sys

VOICED = dict(zip("かきくけこさしすせそたちつてとはひふへほ", "がぎぐげござじずぜぞだぢづでどばびぶべぼ"))
P_SOUND = dict(zip("はひふへほ", "ぱぴぷぺぽ"))
RENYOU = dict(zip("うくぐすつぬぶむる", "いきぎしちにびみり"))
AFTER_SOKUON = set("かきくけこさしすせそたちつてとぱぴぷぺぽ")


def hiragana(text):
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in text)


def load(path):
    """kanji -> set of (reading, kind), kind 'on' or 'kun' (the name readings count as kun)."""
    readings = {}
    literal = None
    for line in gzip.open(path, "rt", encoding="utf-8"):
        m = re.search(r"<literal>(.)</literal>", line)
        if m:
            literal = m.group(1)
            readings[literal] = set()
            continue
        m = re.search(r'<reading r_type="ja_(on|kun)">([^<]+)</reading>|<nanori>([^<]+)</nanori>', line)
        if not m or literal is None:
            continue
        if m.group(3):
            readings[literal].add((m.group(3), "kun"))
        elif m.group(1) == "on":
            readings[literal].add((hiragana(m.group(2)), "on"))
        else:
            text = m.group(2).strip("-")
            stem, _, okurigana = text.partition(".")
            if not okurigana:
                readings[literal].add((stem, "kun"))
            else:
                readings[literal].add((stem + okurigana, "kun"))
                if okurigana.endswith("る") and len(okurigana) > 1:
                    readings[literal].add((stem + okurigana[:-1], "kun"))
                if okurigana[-1] in RENYOU:
                    readings[literal].add((stem + okurigana[:-1] + RENYOU[okurigana[-1]], "kun"))
    return readings


def forms(reading, kind, first, after, last):
    """The forms a reading may take at its place in the word."""
    found = {reading}
    if not first and reading:
        if kind == "kun" and reading[0] in VOICED:
            found.add(VOICED[reading[0]] + reading[1:])
        if kind == "on" and after and after[-1] in "んっ":
            if reading[0] in VOICED:
                found.add(VOICED[reading[0]] + reading[1:])
            if reading[0] in P_SOUND:
                found.add(P_SOUND[reading[0]] + reading[1:])
    if not last:
        found |= {f[:-1] + "っ" for f in list(found) if len(f) > 1 and f[-1] in "つくちき"}
    return found


def readable(word, reading, readings):
    """Whether the reading is made of a reading of every character of the word."""
    def options(i):
        c = word[i]
        if c == "々" and i > 0:
            return options(i - 1)
        if c in "ヶケ":
            return {("が", "kun"), ("か", "kun"), ("こ", "kun")}
        if "ァ" <= c <= "ヺ" or c == "ー":
            return {(hiragana(c), "kana")}
        return readings.get(c, set())

    ends = {(0, "")}  # (position in the reading, the reading of the last character)
    for i in range(len(word)):
        following = set()
        for position, before in ends:
            for text, kind in options(i):
                for form in forms(text, kind, i == 0, before, i == len(word) - 1):
                    if before.endswith("っ") and form[:1] not in AFTER_SOKUON:
                        continue
                    if form and reading.startswith(form, position):
                        following.add((position + len(form), form))
        ends = following
        if not ends:
            return False
    return any(position == len(reading) for position, _ in ends)


def main():
    readings = load(sys.argv[1])
    for line in sys.stdin:
        columns = line.rstrip("\n").split("\t")
        if len(columns) >= 2 and readable(columns[1], columns[0], readings):
            sys.stdout.write(line)


if __name__ == "__main__":
    main()
