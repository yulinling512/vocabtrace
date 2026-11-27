# 桌面端补丁：统一 AI 词卡 + 本地 ECDICT 词典

这是 **补丁**，不是版本更新。

- 不修改 `desktop/package.json` 的版本号
- 不创建 release / tag
- 目标分支：`main`

## 包含的改动

1. 顶栏四角 20px 圆角 + 柔和阴影，账号入口胶囊化，右侧不重叠。
2. 首页三卡：Today's Word / Weekly Pulse 左侧上下，News Break 右侧跨两行；每条新闻配图。
3. 查词页统一为 AI 词卡外观：英文、音标、中文释义先显示；“词源 / 记忆 / 例句 / 搭配”用“AI 生成中”骨架占位，生成后原地替换。
4. 新增本地 ECDICT 英汉词典（769,031 条），`/api/dict` 二分查找，离线可用。
5. 查词输入框在完整词卡生成后清空；AI 失败保留原词。
6. 点击查询即写入生词本，先占位“释义待补全”，词典/AI 完成后再更新，同词不重复。

## 应用方式

补丁按行拆成 4 段，避免单次上传过大：

```powershell
$parts = Get-ChildItem .\desktop-ui-dict.patch.part*.patch | Sort-Object Name
Get-Content $parts.FullName -Raw | Set-Content .\desktop-ui-dict.patch -Encoding utf8
```

然后从仓库根目录应用：

```bash
git apply desktop-ui-dict.patch
```

没有 git 的话，用 VS Code 的“应用补丁”或 `patch -p1 < desktop-ui-dict.patch`。
