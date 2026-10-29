"""Tests of slm_ime_dict.py: packs are composed into one sorted Anthy dictionary, and the user's own words survive."""
import argparse
import os
import tempfile
import unittest

import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import slm_ime_dict as d  # noqa: E402


class PackTest(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        os.environ["SLM_IME_DICT_DIR"] = os.path.join(self.dir.name, "store")
        self.anthy = os.path.join(self.dir.name, "private_words_default")

    def tearDown(self):
        self.dir.cleanup()

    def skk(self, name, text):
        path = os.path.join(self.dir.name, name)
        with open(path, "w", encoding="euc-jp") as f:
            f.write(text)
        return path

    def add(self, name, path):
        d.cmd_add(argparse.Namespace(name=name, path=path, format="skk", encoding="euc-jp", levels="SABC",
                                     source=None, license=None))

    def build(self):
        d.cmd_build(argparse.Namespace(output=self.anthy, dry_run=False))
        with open(self.anthy, encoding="utf-8") as f:
            return f.read().splitlines()

    def test_the_file_is_sorted_by_reading_and_has_no_duplicate(self):
        self.add("a", self.skk("a", "せいど /制度/精度/\nあい /愛/\n"))
        self.add("b", self.skk("b", "せいど /制度/\nいし /医師/\n"))
        lines = self.build()
        self.assertEqual(["あい #T00*1 愛", "いし #T00*1 医師", "せいど #T00*1 制度", "せいど #T00*1 精度"], lines)

    def test_a_pack_that_is_switched_off_is_left_out(self):
        self.add("a", self.skk("a", "あい /愛/\n"))
        self.add("b", self.skk("b", "いし /医師/\n"))
        d.cmd_switch(argparse.Namespace(name="b"), False)
        self.assertEqual(["あい #T00*1 愛"], self.build())

    def test_a_word_of_the_user_is_kept_and_a_removed_pack_goes(self):
        self.add("a", self.skk("a", "あい /愛/\n"))
        self.build()
        with open(self.anthy, "a", encoding="utf-8") as f:
            f.write("おさむ #T00*1 治\n")
        with self.assertRaises(SystemExit):  # its words are still in the file
            d.cmd_remove(argparse.Namespace(name="a", anthy=self.anthy))
        d.cmd_switch(argparse.Namespace(name="a"), False)
        self.assertEqual(["おさむ #T00*1 治"], self.build())
        d.cmd_remove(argparse.Namespace(name="a", anthy=self.anthy))
        self.assertEqual(["おさむ #T00*1 治"], self.build())


if __name__ == "__main__":
    unittest.main()
