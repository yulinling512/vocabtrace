# 桌面端补丁 r2：AI 主题卡片 + 旧版主题 + 体验修正

这是 **补丁**，不是版本更新。

- 不修改 `desktop/package.json` 版本号
- 不创建 release / tag
- 目标分支：`main`

## 补丁包

完整补丁包（含当前 `app/index.html`、`desktop/main.js`、两段补丁与说明）：

[下载 vocabtrace-desktop-patch-20261127-r2.zip](https://aka.doubaocdn.com/s/WVQZMdGVNU)

`app/index.html` SHA256：`5DB133C9FAB18AFFE936F33F9109657C320A14C8DCB8EF57F59A432CA45BDA39`

## 本次补丁的改动

1. 首页顶部大卡、每日一词、周脉冲、News 卡、学习工具卡全部接入主题色，不再各自写死一套配色。
2. AI 配色新增 `newsBg` / `toolsBg` 两块卡片底色字段；提示词要求它们和页面环境有可感知区分、同时仍属于同一主题，正文对比度按 4.8:1 兜底。
3. 主题区新增“旧版”内置主题：暖纸底、绿棕大卡、奶油每日卡、薄荷周卡、浅蓝 News、旧版多色工具卡。
4. 电脑端首页背景加入极慢漂移与网格呼吸；关闭动效即停止，手机端不启用。
5. 首页大卡左上角的 L 形书签色块改为与栏目一致的小圆点。
6. 词汇量测试每道题新增“不知道”，固定 10 秒倒计时，超时按“不知道”记录。
7. “长句默写”更名为“长句拆译”，副标题“拆开结构 · 译准意思”；入口、历史筛选与判分页标题同步。

## 应用

优先用补丁包直接覆盖：

1. 备份原文件；
2. 用包内 `app/index.html` 覆盖仓库 `app/index.html`；
3. 用包内 `desktop/main.js` 覆盖仓库 `desktop/main.js`；
4. 重启桌面端。

也可以按顺序打补丁：

```bash
git apply desktop-ui-dict.patch
git apply ui-fix-20261127-r2.patch
```

本地词典数据（`数据/词典/ecdict.bin`、`ecdict.idx`）不打进补丁包；放到程序数据目录即可离线查词。
