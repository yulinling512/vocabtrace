# -*- coding: utf-8 -*-
"""给词条补「联想记忆」：写入 hook.tip，其余字段一律不动。

用法: python apply-tips.py [tips文件] [账号json]
安全: 自动备份 .bak-时间戳；只增字段，不碰 prog / session / books。
"""
import json, os, sys, time, shutil, io

HERE = os.path.dirname(os.path.abspath(__file__))
ACCT = os.path.join(HERE, "..", "数据", "账号", "umwwdj45i7f43.json")

src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "_tips", "t01.txt")
acct = sys.argv[2] if len(sys.argv) > 2 else ACCT

pairs = []
MODES = ("谐音", "拆字", "画面", "动作", "对比", "故事", "拟声", "场景")
with io.open(src, encoding="utf-8") as f:
    for ln in f:
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        p = ln.split("|", 2)
        if len(p) == 2:
            w, mode, t = p[0].strip(), "助记", p[1].strip()
        elif len(p) == 3:
            w, mode, t = p[0].strip(), p[1].strip(), p[2].strip()
        else:
            continue
        if w and t:
            pairs.append((w, mode if mode in MODES else "助记", t))

d = json.load(io.open(acct, encoding="utf-8"))
before = {k: json.loads(json.dumps(d[k])) for k in ("prog", "session")}
before_books_ses = [json.dumps(b.get("session"), ensure_ascii=False) for b in d.get("books", [])]

# 词卡可能在顶层 words，也可能内嵌在 books[].words（前端读的是书架那份）
lists = [d["words"]] + [b["words"] for b in d.get("books", []) if isinstance(b.get("words"), list)]
hit = miss = 0
for w, mode, t in pairs:
    found = False
    for lst in lists:
        for x in lst:
            if x.get("word") == w:
                x.setdefault("hook", {})
                x["hook"]["tip"] = t
                x["hook"]["mode"] = mode
                found = True
    if found:
        hit += 1
    else:
        print("  未找到:", w); miss += 1

bk = acct + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(acct, bk)
d["savedAt"] = int(time.time() * 1000)
json.dump(d, io.open(acct, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

# 校验
d2 = json.load(io.open(acct, encoding="utf-8"))
same = all(d2[k] == before[k] for k in ("prog", "session")) and [json.dumps(b.get("session"), ensure_ascii=False) for b in d2.get("books", [])] == before_books_ses
tips = sum(1 for x in d2["words"] if (x.get("hook") or {}).get("tip"))
btips = sum(1 for x in d2.get("books",[{}])[0].get("words",[]) if (x.get("hook") or {}).get("tip"))
print("写入 %d 条，未匹配 %d 条" % (hit, miss))
print("进度/会话未变:", same, "| session.index =", d2["session"]["index"], "right =", d2["session"]["right"])
print("顶层带记法:", tips, "/", len(d2["words"]), "| 书架内带记法:", btips)
print("备份:", os.path.basename(bk))
