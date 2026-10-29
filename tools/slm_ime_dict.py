#!/usr/bin/env python3
"""
Manage domain dictionaries (packs) for the Anthy private dictionary that fcitx5-slm-ime uses for the alternative kanji.

A pack is one list of words of a field (law, medicine, biology, ...) in the SKK form "reading /word1/word2/". The packs
are kept in a directory, each can be switched on and off, and `build` composes the Anthy private dictionary
(~/.anthy/private_words_default) from the packs that are on. The file is composed whole, because Anthy reads it as a
list sorted by reading, and because `anthy-dic-tool --load` replaces the dictionary and rewrites the file for every word,
which takes minutes for a few thousand words.

  slm_ime_dict.py list
  slm_ime_dict.py add NAME PATH [--format skk|manbyo] [--encoding euc-jp] [--source TEXT] [--license TEXT]
  slm_ime_dict.py enable NAME | disable NAME | remove NAME
  slm_ime_dict.py build [--output PATH] [--dry-run]
  slm_ime_dict.py check [--samples 100] [--url http://localhost:8190]

Words that are in the Anthy file but in no pack (the words that the user registered) are kept by `build`. Restart the
conversion server after a build (`systemctl --user restart slm-ime-server`): Anthy reads the file when it starts.
The directory is $SLM_IME_DICT_DIR, or ~/.local/share/slm-ime/dictionaries.
"""
import argparse
import json
import os
import random
import shutil
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import manbyo2skk  # noqa: E402
import skk2anthy  # noqa: E402

TAG = "#T00*1"  # a noun of frequency 1, the tag that skk2anthy.py gives to every word
ANTHY_FILE = os.path.expanduser("~/.anthy/private_words_default")


def store_dir():
    return os.environ.get("SLM_IME_DICT_DIR") or os.path.expanduser("~/.local/share/slm-ime/dictionaries")


def index_path():
    return os.path.join(store_dir(), "packs.json")


def load_index():
    if not os.path.exists(index_path()):
        return {"packs": []}
    with open(index_path(), encoding="utf-8") as f:
        return json.load(f)


def save_index(index):
    os.makedirs(store_dir(), exist_ok=True)
    with open(index_path(), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
        f.write("\n")


def find(index, name):
    for pack in index["packs"]:
        if pack["name"] == name:
            return pack
    sys.exit(f"no pack named {name}")


def pack_entries(pack):
    """Yield (reading, word) from the SKK file of a pack."""
    path = os.path.join(store_dir(), pack["file"])
    for reading, words in skk2anthy.entries(path, "utf-8"):
        for word in words:
            yield reading, word


def read_anthy_lines(path):
    """The (reading, word) pairs of an Anthy private dictionary file, in the order of the file."""
    pairs = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if not line.strip():
                    continue
                reading, _, rest = line.partition(" ")
                _tag, _, word = rest.partition(" ")
                pairs.append((reading, word))
    return pairs


def cmd_list(_args):
    index = load_index()
    if not index["packs"]:
        print("no packs")
    for pack in index["packs"]:
        print(f"{'on ' if pack['enabled'] else 'off'} {pack['name']:<16} {pack['entries']:>7} words  "
              f"{pack.get('license', '-')}  ({pack.get('source', '-')})")


def cmd_add(args):
    index = load_index()
    if any(p["name"] == args.name for p in index["packs"]):
        sys.exit(f"a pack named {args.name} exists; remove it first")
    if args.format == "manbyo":
        source = ((reading, [form]) for reading, form in manbyo2skk.entries(args.path, args.levels))
    else:
        source = skk2anthy.entries(args.path, args.encoding)
    os.makedirs(store_dir(), exist_ok=True)
    file_name = f"{args.name}.skk"
    count = 0
    seen = set()
    with open(os.path.join(store_dir(), file_name), "w", encoding="utf-8") as out:
        for reading, words in source:
            fresh = [w for w in words if (reading, w) not in seen]
            seen.update((reading, w) for w in fresh)
            if fresh:
                out.write(f"{reading} /{'/'.join(fresh)}/\n")
                count += len(fresh)
    index["packs"].append({"name": args.name, "enabled": True, "file": file_name, "entries": count,
                           "source": args.source or os.path.basename(args.path), "license": args.license or "-",
                           "added": time.strftime("%Y-%m-%d")})
    save_index(index)
    print(f"added {args.name}: {count} words (on); run `build` and restart the server")


def cmd_switch(args, enabled):
    index = load_index()
    find(index, args.name)["enabled"] = enabled
    save_index(index)
    print(f"{args.name}: {'on' if enabled else 'off'}; run `build` and restart the server")


def cmd_remove(args):
    index = load_index()
    pack = find(index, args.name)
    # Once the pack is gone, its words in the Anthy file would look like words that the user registered.
    still_there = set(read_anthy_lines(args.anthy or ANTHY_FILE)) & set(pack_entries(pack))
    if still_there and pack["enabled"]:
        sys.exit(f"{args.name} is on: switch it off and run `build` first, so that its words leave the Anthy file")
    if still_there:
        sys.exit(f"{len(still_there)} words of {args.name} are still in the Anthy file: run `build` first")
    index["packs"].remove(pack)
    path = os.path.join(store_dir(), pack["file"])
    if os.path.exists(path):
        os.remove(path)
    save_index(index)
    print(f"removed {args.name}; run `build` and restart the server")


def compose(index, current_pairs):
    """The pairs of the new dictionary, sorted by reading; and the number of kept words of the user."""
    managed = set()
    for pack in index["packs"]:
        managed.update(pack_entries(pack))
    kept = [pair for pair in current_pairs if pair not in managed]
    pairs = list(kept)
    seen = set(kept)
    for pack in index["packs"]:
        if not pack["enabled"]:
            continue
        for pair in pack_entries(pack):
            if pair not in seen:
                seen.add(pair)
                pairs.append(pair)
    pairs.sort(key=lambda pair: pair[0])  # stable: for one reading, the order of the sources stays
    return pairs, len(set(kept))


def cmd_build(args):
    index = load_index()
    output = args.output or ANTHY_FILE
    pairs, own = compose(index, read_anthy_lines(output))
    on = [p for p in index["packs"] if p["enabled"]]
    print(f"{len(pairs)} words = {own} registered by the user + {len(pairs) - own} from "
          f"{len(on)} pack(s): {', '.join(p['name'] for p in on) or '-'}")
    if args.dry_run:
        return
    if os.path.exists(output):
        backup_dir = os.path.join(store_dir(), "backup")
        os.makedirs(backup_dir, exist_ok=True)
        backup = os.path.join(backup_dir, f"{os.path.basename(output)}.{time.strftime('%Y%m%d-%H%M%S')}")
        shutil.copy2(output, backup)
        print(f"backup: {backup}")
    os.makedirs(os.path.dirname(output), exist_ok=True)
    temporary = output + ".new"
    with open(temporary, "w", encoding="utf-8") as f:
        for reading, word in pairs:
            f.write(f"{reading} {TAG} {word}\n")
    os.chmod(temporary, 0o600)
    os.replace(temporary, output)
    print(f"written: {output}; restart the conversion server (systemctl --user restart slm-ime-server)")


def cmd_check(args):
    index = load_index()
    rng = random.Random(args.seed)
    for pack in index["packs"]:
        if not pack["enabled"]:
            continue
        pairs = list(pack_entries(pack))
        sample = rng.sample(pairs, min(args.samples, len(pairs)))
        found = 0
        for reading, word in sample:
            body = json.dumps({"input": reading, "n": 50}).encode()
            request = urllib.request.Request(args.url + "/api/segment-candidates", data=body,
                                             headers={"content-type": "application/json"})
            with urllib.request.urlopen(request, timeout=60) as response:
                if word in json.load(response)["candidates"]:
                    found += 1
        print(f"{pack['name']:<16} {found}/{len(sample)} of the sampled words are among the candidates")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list").set_defaults(run=cmd_list)
    add = sub.add_parser("add")
    add.add_argument("name")
    add.add_argument("path")
    add.add_argument("--format", choices=["skk", "manbyo"], default="skk")
    add.add_argument("--encoding", default="euc-jp", help="of an SKK file")
    add.add_argument("--levels", default="SABC", help="reliability levels of a ManbyoDic file")
    add.add_argument("--source")
    add.add_argument("--license")
    add.set_defaults(run=cmd_add)
    for name, enabled in (("enable", True), ("disable", False)):
        s = sub.add_parser(name)
        s.add_argument("name")
        s.set_defaults(run=lambda a, e=enabled: cmd_switch(a, e))
    remove = sub.add_parser("remove")
    remove.add_argument("name")
    remove.add_argument("--anthy", help="the Anthy dictionary file to look in (default: ~/.anthy/private_words_default)")
    remove.set_defaults(run=cmd_remove)
    build = sub.add_parser("build")
    build.add_argument("--output")
    build.add_argument("--dry-run", action="store_true")
    build.set_defaults(run=cmd_build)
    check = sub.add_parser("check")
    check.add_argument("--samples", type=int, default=100)
    check.add_argument("--url", default="http://localhost:8190")
    check.add_argument("--seed", type=int, default=1)
    check.set_defaults(run=cmd_check)
    args = parser.parse_args()
    args.run(args)


if __name__ == "__main__":
    main()
