# -*- coding: utf-8 -*-
"""把 _cards/*.txt 里的完整词卡并进账号数据与进度数据。

单条格式（@@ 开头一条，字段行可缺）：
  @@word
  C: 拆形 || 一句钩子      —— hook.cut / hook.line
  E: 英文例句 ~ 中文        —— eg（可多行）
  L: 搭配1 / 搭配2 / 搭配3  —— col
  T: tone emoji            —— tone / icon
  M: 易混词 ~ 差别          —— mix

只填空位，已有内容一律不覆盖；写前自动备份。
用法：python apply-cards.py [--dry]
"""
import io
import json
import os
import shutil
import sys
import time

ROOT = r"D:\VocabLab"
SRC = os.path.join(ROOT, "源码")
DATA = os.path.join(ROOT, "数据")
CARD_DIR = os.path.join(SRC, "_cards")

TONES = {"warm", "cool", "dark", "bright", "calm", "sharp"}


def load_cards():
    cards = {}
    if not os.path.isdir(CARD_DIR):
        return cards
    for name in sorted(os.listdir(CARD_DIR)):
        if not name.endswith(".txt"):
            continue
        cur = None
        for raw in io.open(os.path.join(CARD_DIR, name), encoding="utf-8"):
            line = raw.rstrip("\n").strip()
            if not line:
                continue
            if line.startswith("@@"):
                cur = {"word": line[2:].strip(), "eg": [], "col": [], "mix": []}
                cards[cur["word"]] = cur
                continue
            if cur is None or len(line) < 2 or line[1] != ":":
                continue
            tag, body = line[0], line[2:].strip()
            if tag == "C" and "||" in body:
                cut, hook = body.split("||", 1)
                cur["cut"] = cut.strip()
                cur["line"] = hook.strip()
            elif tag == "E" and "~" in body:
                en, cn = body.split("~", 1)
                cur["eg"].append([en.strip(), cn.strip()])
            elif tag == "L":
                cur["col"] = [x.strip() for x in body.split("/") if x.strip()]
            elif tag == "T":
                parts = body.split()
                if parts and parts[0] in TONES:
                    cur["tone"] = parts[0]
                    if len(parts) > 1:
                        cur["icon"] = parts[1]
            elif tag == "M" and "~" in body:
                a, b = body.split("~", 1)
                cur["mix"].append([a.strip(), b.strip()])
    return cards


def fill(words, cards):
    n = 0
    for w in words:
        c = cards.get(w.get("word", ""))
        if not c:
            continue
        touched = False
        hook = w.get("hook") or {}
        if c.get("cut") and not hook.get("cut"):
            hook["cut"] = c["cut"]
            if c.get("line"):
                hook["line"] = c["line"]
            w["hook"] = hook
            touched = True
        if c["eg"] and not w.get("eg"):
            w["eg"] = c["eg"]
            touched = True
        if c["col"] and not w.get("col"):
            w["col"] = c["col"]
            touched = True
        if c["mix"] and not w.get("mix"):
            w["mix"] = c["mix"]
            touched = True
        if c.get("tone") and not w.get("tone"):
            w["tone"] = c["tone"]
            touched = True
        if c.get("icon") and not w.get("icon"):
            w["icon"] = c["icon"]
            touched = True
        if touched:
            n += 1
    return n


def main():
    dry = "--dry" in sys.argv
    cards = load_cards()
    if not cards:
        print("没有找到词卡文件")
        return
    print("词卡：%d 个词" % len(cards))

    stamp = time.strftime("%Y%m%d-%H%M%S")
    targets = [os.path.join(DATA, "进度数据.json")]
    acct = os.path.join(DATA, "账号")
    if os.path.isdir(acct):
        for n in sorted(os.listdir(acct)):
            if n.endswith(".json") and n != "账号表.json":
                targets.append(os.path.join(acct, n))

    now = int(time.time() * 1000)
    for p in targets:
        if not os.path.exists(p):
            continue
        d = json.load(io.open(p, encoding="utf-8"))
        cnt = 0
        for b in d.get("books") or []:
            cnt += fill(b.get("words") or [], cards)
        if d.get("words"):
            cnt += fill(d["words"], cards)
        if dry:
            print("  [dry] %s → %d 个词" % (os.path.basename(p), cnt))
            continue
        d["savedAt"] = now
        if not os.path.exists(p + ".bak-" + stamp):
            shutil.copy2(p, p + ".bak-" + stamp)
        io.open(p, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False))
        print("  %s → 补全 %d 个词，savedAt=%d" % (os.path.basename(p), cnt, now))

    if not dry:
        total = sum(1 for w in (json.load(io.open(targets[0], encoding="utf-8")).get("books") or [{}])[0].get("words", []) if (w.get("eg") or []))
        print("进度数据.json 中有例句的词：%d" % total)


if __name__ == "__main__":
    main()
