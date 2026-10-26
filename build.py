#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build Microsoft Pinyin lexicon for Diablo IV + Diablo II: Resurrected.

Cross-game merge: if a Chinese phrase already exists in D4, drop all D2R
entries for that phrase (regardless of pinyin). Alternate pinyin triggers
for the same phrase within one game are kept.
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "source"))
sys.path.insert(0, str(ROOT / "tools"))

from pypinyin import Style, lazy_pinyin
from d4_words import D4
from d2r_words import D2R


def to_pinyin(word: str) -> str:
    parts = lazy_pinyin(word, style=Style.NORMAL)
    s = "".join(parts).lower()
    return re.sub(r"[^a-z]", "", s)


def valid_entry(pinyin: str, phrase: str) -> tuple[bool, str]:
    if not phrase:
        return False, "empty phrase"
    if len(phrase) > 64:
        return False, "phrase >64"
    if not pinyin:
        return False, "empty pinyin"
    if len(pinyin) > 32:
        return False, "pinyin >32"
    if pinyin[0] in ("u", "v"):
        return False, "pinyin starts with u/v"
    if not re.fullmatch(r"[a-z]+", pinyin):
        return False, "pinyin not a-z"
    return True, ""


def collect(raw, tag):
    seen = set()
    out = []
    skipped = []
    for py_override, phrase in raw:
        phrase = phrase.strip()
        py = (py_override or to_pinyin(phrase)).lower().strip()
        py = re.sub(r"[^a-z]", "", py)
        ok, reason = valid_entry(py, phrase)
        if not ok:
            skipped.append((phrase, py, reason))
            continue
        key = (py, phrase)
        if key in seen:
            continue
        seen.add(key)
        out.append((py, phrase, tag))
    if skipped:
        print(f"[{tag}] skipped {len(skipped)}:")
        for row in skipped[:20]:
            print("  ", row)
    return out


def assign_positions(entries):
    by_py = defaultdict(list)
    order = []
    for py, phrase, tag in entries:
        if py not in by_py:
            order.append(py)
        if any(p == phrase for p, _ in by_py[py]):
            continue
        by_py[py].append((phrase, tag))
    result = []
    overflow = 0
    for py in order:
        items = by_py[py]
        for i, (phrase, tag) in enumerate(items[:9]):
            result.append((py, i + 1, phrase, tag))
        if len(items) > 9:
            overflow += len(items) - 9
    if overflow:
        print(f"warning: {overflow} dropped (>9/pinyin)")
    return result


def write_pinyinlex_txt(path, rows):
    path.write_text("\n".join(f"{py}\t{pos}\t{phrase}" for py, pos, phrase, _ in rows) + "\n", encoding="utf-8")


def build_dat(rows, out_dat):
    from mschxudp_file import MschxudpFileBuilder
    b = MschxudpFileBuilder(win10="1703")
    for py, pos, phrase, _ in rows:
        b.add_phrase((pos, 6), py, phrase)
    b.save(str(out_dat))


def main():
    d4 = collect(D4, "d4")
    d2r = collect(D2R, "d2r")

    d4_phrase_set = {phrase for _, phrase, _ in d4}
    d2r_kept = []
    d2r_overlap_entries = 0
    d2r_overlap_phrases = set()
    for py, phrase, tag in d2r:
        if phrase in d4_phrase_set:
            d2r_overlap_entries += 1
            d2r_overlap_phrases.add(phrase)
            continue
        d2r_kept.append((py, phrase, tag))

    merged = d4 + d2r_kept
    # safety dedupe exact (py,phrase)
    seen = set()
    merged_u = []
    for py, phrase, tag in merged:
        key = (py, phrase)
        if key in seen:
            continue
        seen.add(key)
        merged_u.append((py, phrase, tag))

    d4_rows = assign_positions(d4)
    d2r_rows = assign_positions(d2r)
    all_rows = assign_positions(merged_u)

    write_pinyinlex_txt(ROOT / "d4.txt", d4_rows)
    write_pinyinlex_txt(ROOT / "d2r.txt", d2r_rows)
    write_pinyinlex_txt(ROOT / "diablo-microsoft-pinyin.txt", all_rows)
    build_dat(d4_rows, ROOT / "d4.dat")
    build_dat(d2r_rows, ROOT / "d2r.dat")
    build_dat(all_rows, ROOT / "diablo-microsoft-pinyin.dat")
    text = (ROOT / "diablo-microsoft-pinyin.txt").read_text(encoding="utf-8")
    (ROOT / "diablo-microsoft-pinyin-utf8bom.txt").write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))

    stats = {
        "d4_entries": len(d4_rows),
        "d4_phrases": len({r[2] for r in d4_rows}),
        "d2r_raw_entries": len(d2r),
        "d2r_entries": len(d2r_rows),
        "d2r_phrases": len({r[2] for r in d2r_rows}),
        "d2r_overlap_phrases_with_d4": len(d2r_overlap_phrases),
        "d2r_overlap_entries_dropped": d2r_overlap_entries,
        "d2r_entries_added_to_merge": len(d2r_kept),
        "merged_entries": len(all_rows),
        "merged_phrases": len({r[2] for r in all_rows}),
        "unique_pinyin": len({r[0] for r in all_rows}),
    }
    (ROOT / "STATS.txt").write_text("\n".join(f"{k}={v}" for k, v in stats.items()) + "\n", encoding="utf-8")
    print("STATS:")
    for k, v in stats.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
