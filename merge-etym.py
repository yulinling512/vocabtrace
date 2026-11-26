# -*- coding: utf-8 -*-
"""把 _etym/*.txt 里的词源并进账号数据。格式：word|词源正文（一行一条）。
只填空位；写前备份；更新 savedAt 让应用读到新数据。
"""
import io
import json
import os
import shutil
import time

ROOT = r"D:\VocabLab"
DATA = os.path.join(ROOT, "数据")
ETY = os.path.join(ROOT, "源码", "_etym")


def load():
    out = {}
    if not os.path.isdir(ETY):
        return out
    for n in sorted(os.listdir(ETY)):
        if not n.endswith(".txt"):
            continue
        for line in io.open(os.path.join(ETY, n), encoding="utf-8"):
            line = line.strip()
            if not line or "|" not in line:
                continue
            w, t = line.split("|", 1)
            if t.strip():
                out[w.strip()] = t.strip()
    return out


def fill(words, et):
    n = 0
    for w in words:
        t = et.get(w.get("word", ""))
        if not t:
            continue
        e = w.get("etymology") or {}
        if (e.get("t") or "").strip():
            continue
        e["t"] = t
        e.setdefault("src", "gen")
        e.setdefault("r", [])
        w["etymology"] = e
        n += 1
    return n


def main():
    et = load()
    print("词源条目：%d" % len(et))
    stamp = time.strftime("%Y%m%d-%H%M%S")
    now = int(time.time() * 1000)
    targets = [os.path.join(DATA, "进度数据.json")]
    acct = os.path.join(DATA, "账号")
    if os.path.isdir(acct):
        for n in sorted(os.listdir(acct)):
            if n.endswith(".json") and n != "账号表.json":
                targets.append(os.path.join(acct, n))
    for p in targets:
        if not os.path.exists(p):
            continue
        d = json.load(io.open(p, encoding="utf-8"))
        cnt = 0
        for b in d.get("books") or []:
            cnt += fill(b.get("words") or [], et)
        if d.get("words"):
            cnt += fill(d["words"], et)
        d["savedAt"] = now
        if not os.path.exists(p + ".bak-" + stamp):
            shutil.copy2(p, p + ".bak-" + stamp)
        io.open(p, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False))
        print("  %s → 补 %d 处" % (os.path.basename(p), cnt))


if __name__ == "__main__":
    main()
