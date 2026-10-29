"""Tests of reading_check.readable, with a few readings written here instead of KANJIDIC2."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
from reading_check import readable

READINGS = {
    "交": {("こう", "on")}, "流": {("りゅう", "on"), ("る", "on"), ("ながれる", "kun"), ("ながれ", "kun")},
    "手": {("て", "kun"), ("しゅ", "on")}, "間": {("ま", "kun"), ("かん", "on")},
    "個": {("こ", "on")}, "学": {("がく", "on")}, "校": {("こう", "on")},
    "発": {("はつ", "on")}, "表": {("ひょう", "on")}, "人": {("ひと", "kun"), ("じん", "on")},
    "番": {("ばん", "on")}, "組": {("くむ", "kun"), ("くみ", "kun"), ("そ", "on")},
    "一": {("いち", "on")}, "時": {("じ", "on")}, "期": {("き", "on")},
}


class ReadableTest(unittest.TestCase):
    def test_right_readings(self):
        for word, reading in [("交流", "こうりゅう"), ("手間", "てま"), ("個々", "ここ"), ("学校", "がっこう"),
                              ("発表", "はっぴょう"), ("人々", "ひとびと"), ("番組", "ばんぐみ"),
                              ("一時期", "いちじき")]:
            self.assertTrue(readable(word, reading, READINGS), word + " " + reading)

    def test_wrong_readings(self):
        for word, reading in [("交流", "こうりょう"), ("手間", "てまえ"), ("個々", "こここ"), ("番組", "ばんぐ"),
                              ("一時期", "いっじき")]:
            self.assertFalse(readable(word, reading, READINGS), word + " " + reading)


if __name__ == "__main__":
    unittest.main()
