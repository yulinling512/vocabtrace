# -*- coding: utf-8 -*-
"""把 _s1.._s6.txt 里的补充义项并进账号数据与词库 CSV。

补丁行格式：word|pos. 释义
只追加「原数据里没有的义项」，不覆盖、不删除原有内容。
用法：python merge-senses.py
"""
import csv
import io
import json
import os
import re
import shutil
import time

ROOT = r"D:\VocabLab"
SRC = os.path.join(ROOT, "源码")
DATA = os.path.join(ROOT, "数据")


def load_patch():
    patch = {}
    for i in range(1, 7):
        p = os.path.join(SRC, "_s%d.txt" % i)
        if not os.path.exists(p):
            continue
        for line in io.open(p, encoding="utf-8"):
            line = line.strip()
            if not line or "|" not in line:
                continue
            word, rest = line.split("|", 1)
            word = word.strip()
            rest = rest.strip()
            m = re.match(r"^([a-z]+\.)\s*(.+)$", rest)
            if m:
                pos, mean = m.group(1), m.group(2).strip()
            else:
                pos, mean = "", rest
            patch.setdefault(word, []).append((pos, mean))
    return patch


def merge_into_words(words, patch):
    added = 0
    touched = 0
    for w in words:
        adds = patch.get(w.get("word", ""))
        if not adds:
            continue
        senses = w.get("senses") or []
        have = {(s.get("pos", "").strip(), s.get("meaning", "").strip()) for s in senses}
        have_mean = {s.get("meaning", "").strip() for s in senses}
        before = len(senses)
        for pos, mean in adds:
            if (pos, mean) in have or mean in have_mean:
                continue
            senses.append({"pos": pos, "meaning": mean})
            have.add((pos, mean))
            have_mean.add(mean)
        if len(senses) > before:
            w["senses"] = senses
            added += len(senses) - before
            touched += 1
    return added, touched


def do_json(path, patch):
    d = json.load(io.open(path, encoding="utf-8"))
    books = d.get("books") or []
    a = t = 0
    for b in books:
        x, y = merge_into_words(b.get("words") or [], patch)
        a += x
        t += y
    # 旧版单份数据里也可能有顶层 words
    if d.get("words"):
        x, y = merge_into_words(d["words"], patch)
        a += x
        t += y
    io.open(path, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False))
    return a, t


def do_csv(path, patch):
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        return 0
    head = rows[0]
    iw = head.index("word")
    im = head.index("meanings")
    added = 0
    for r in rows[1:]:
        if len(r) <= max(iw, im):
            continue
        adds = patch.get(r[iw].strip())
        if not adds:
            continue
        cur = [x.strip() for x in r[im].split("|") if x.strip()]
        cur_mean = set()
        for x in cur:
            m = re.match(r"^[a-z]+\.\s*(.+)$", x)
            cur_mean.add((m.group(1) if m else x).strip())
        for pos, mean in adds:
            if mean in cur_mean:
                continue
            cur.append((pos + " " + mean).strip())
            cur_mean.add(mean)
            added += 1
        r[im] = " | ".join(cur)
    with io.open(path, "w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f, quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n").writerows(rows)
    return added


def main():
    patch = load_patch()
    print("补丁词条：%d 个词，%d 条义项" % (len(patch), sum(len(v) for v in patch.values())))

    stamp = time.strftime("%Y%m%d-%H%M%S")
    targets = [os.path.join(DATA, "进度数据.json")]
    acct_dir = os.path.join(DATA, "账号")
    if os.path.isdir(acct_dir):
        for n in os.listdir(acct_dir):
            if n.endswith(".json") and n != "账号表.json":
                targets.append(os.path.join(acct_dir, n))

    for p in targets:
        if not os.path.exists(p):
            continue
        shutil.copy2(p, p + ".bak-" + stamp)
        a, t = do_json(p, patch)
        print("  %s → 新增 %d 条义项，涉及 %d 个词" % (os.path.basename(p), a, t))

    csv_path = os.path.join(ROOT, "词库", "高频词默写.csv")
    if os.path.exists(csv_path):
        shutil.copy2(csv_path, csv_path + ".bak-" + stamp)
        n = do_csv(csv_path, patch)
        print("  高频词默写.csv → 新增 %d 条义项" % n)


if __name__ == "__main__":
    main()
