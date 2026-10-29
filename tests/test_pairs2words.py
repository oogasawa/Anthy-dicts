"""Tests of pairs2words.word_of. Run: python3 -m unittest discover tests"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
from pairs2words import word_of


class WordOfTest(unittest.TestCase):
    def test_a_noun_and_its_particle(self):
        self.assertEqual(word_of("せいどが", "精度が"), ("せいど", "精度", "が"))

    def test_a_word_of_one_character_is_left_out(self):
        self.assertIsNone(word_of("おちる", "落ちる"))
        self.assertIsNone(word_of("はなが", "花が"))

    def test_a_noun_without_a_tail(self):
        self.assertEqual(word_of("せいど", "精度"), ("せいど", "精度", ""))

    def test_a_reading_that_is_not_hiragana_only_is_left_out(self):
        self.assertIsNone(word_of("30だいぜんはんの", "30代前半の"))
        self.assertIsNone(word_of("アウェーかんは", "アウェー感は"))

    def test_a_noun_before_a_particle_and_punctuation(self):
        self.assertEqual(word_of("せいどが、", "精度が、"), ("せいど", "精度", "が"))

    def test_a_noun_before_punctuation(self):
        self.assertEqual(word_of("しょくしつ！", "職質！"), ("しょくしつ", "職質", ""))

    def test_the_stem_of_a_verb_or_an_adjective_is_left_out(self):
        self.assertIsNone(word_of("かく", "書く"))
        self.assertIsNone(word_of("たかい", "高い"))
        self.assertIsNone(word_of("べんきょうして", "勉強して"))

    def test_a_tail_that_only_starts_with_a_particle_is_left_out(self):
        self.assertIsNone(word_of("あがる", "上がる"))
        self.assertIsNone(word_of("わからない", "分からない"))

    def test_a_run_of_particles_is_a_tail(self):
        self.assertEqual(word_of("がっこうには", "学校には"), ("がっこう", "学校", "には"))

    def test_a_word_with_hiragana_inside_is_left_out(self):
        self.assertIsNone(word_of("とりあいが", "取り合いが"))

    def test_a_word_without_kanji_is_left_out(self):
        self.assertIsNone(word_of("でーたが", "データが"))


if __name__ == "__main__":
    unittest.main()
