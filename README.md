# Anthy-dicts

Dictionaries for [Anthy](https://github.com/fujiwarat/anthy-unicode), the Japanese kana-kanji converter, and the
tools that make them.

Anthy misses many everyday words, compound nouns above all: 代車, 職質, 下値圏, 勾留先. The words here are taken
from text whose reading is known, cut into bunsetsu (phrasal units), and only the words that Anthy does not offer
for their reading are kept.

## How the words are made

1. `tools/pairs2words.py` reads reading/text pairs cut into bunsetsu, such as `せいど|が|よい` and `精度|が|よい`.
   It takes the noun out of each bunsetsu by removing the kana tail (the particles and the okurigana, written the
   same in the reading and in the text), and counts how often each noun is seen with its reading. Only the words
   that are nouns for sure are kept; the rules are in the script.
2. `tools/anthy_lacks.py` asks Anthy, through `libanthy`, for the candidates of each reading, and keeps the words
   that are not among them.
3. `tools/reading_check.py` keeps the words whose reading is made of the readings of their characters in
   [KANJIDIC2](https://www.edrdg.org/wiki/index.php/KANJIDIC_Project) (CC BY-SA 4.0). The readings in the pairs were
   given by a language model, and it reads some words wrong again and again (交流 as こうりょう, 手間 as てまえ).

```sh
python3 tools/pairs2words.py PAIRS_DIR... > words.tsv
python3 tools/anthy_lacks.py < words.tsv | python3 tools/reading_check.py kanjidic2.xml.gz > lacks.tsv
```

`anthy_lacks.py` uses the dictionaries of the user who runs it. Anthy finds the home directory in the user
database, not in `$HOME`; to try a dictionary in another directory without touching the one in use, build
`tools/fakehome.c` and run with `LD_PRELOAD=./fakehome.so FAKE_HOME=/that/directory`:

```sh
gcc -shared -fPIC -O2 -o fakehome.so tools/fakehome.c -ldl
```

The pairs come from [fcitx5-slm-ime](https://github.com/oogasawa/fcitx5-slm-ime), which makes them from the Japanese
Wikipedia and FineWeb-2 for the training of its model.

## Other tools

- `tools/slm_ime_dict.py` manages dictionaries by field (packs) and builds the Anthy private dictionary
  (`~/.anthy/private_words_default`) from the packs that are on. The lines of that file must be sorted by reading.
- `tools/skk2anthy.py` converts an SKK dictionary (the entries without okurigana) to Anthy's text form.
- `tools/manbyo2skk.py` converts the Manbyo dictionary of medical terms (CC BY 4.0) to an SKK dictionary.

## Tests

```sh
python3 -m unittest discover tests
```

## License

The tools (`tools/`, `tests/`) are under the Apache License 2.0 (`LICENSE`).

The dictionaries are made from the Japanese Wikipedia (CC BY-SA 4.0) and FineWeb-2 (ODC-By 1.0), and are under
the Creative Commons Attribution-ShareAlike 4.0 International License (`LICENSE-DATA`).
