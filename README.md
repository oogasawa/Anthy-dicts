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

```sh
python3 tools/pairs2words.py PAIRS_DIR... > words.tsv
HOME=/path/to/a/copy python3 tools/anthy_lacks.py < words.tsv > lacks.tsv
```

`anthy_lacks.py` uses the dictionaries of `$HOME/.anthy`. Run it with `HOME` set to a copy, so that the
dictionaries in use are not touched.

The pairs come from [fcitx5-slm-ime](https://github.com/oogasawa/fcitx5-slm-ime), which makes them from the Japanese
Wikipedia and FineWeb-2 for the training of its model.

## Tests

```sh
python3 -m unittest discover tests
```
