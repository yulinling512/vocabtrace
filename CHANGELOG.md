# 更新记录

## 1.1.1 · 2026-11-27

### 新增
- 桌面端查词层：`lookup` 视图、本地词典接口 `/api/dict`、查词卡片、骨架屏、统一词卡
- 桌面端新增视图：生词本 `notebook`、新闻 `news`、训练 `train`、报告 `report`、句子 `sentence`、历史 `history`
- 桌面主进程新增 `/api/news`；数据目录优先跟随程序目录，只读安装目录自动回退用户配置目录
- 安卓端内置精简词典 `assets/dict.js`（约 3.3 MB），离线可查
- Linux 端新增 ARM64 打包脚本与便携包，适配麒麟 990 / 统信 UOS 20

### 打包
- Windows：`词迹-1.1.0-win-portable.zip`（含 44.8 MB 本地词典）
- Android：`词迹-安卓-1.1.1.apk`，versionCode 118
- Linux ARM64：`词迹-1.1.0-linux-arm64.tar.gz`
- 源码：`词迹-源码-1.1.1.zip`

### 已知限制
- 三个平台版本号暂未完全统一：Windows / Linux 为 1.1.0，Android 为 1.1.1
- Linux ARM64 包为交叉组装，未在麒麟 990 真机验证
- 云同步仍为单份快照覆盖，没有历史版本

## 1.0.14 · 2026-11-27

### 修复
- 一组严格等于某一页 PDF 的 36 个词，页内可打乱，跨页不再串词
- 今日目标与当前会话进度统一，不再出现首页 33/36、点进去 21/21 的口径冲突
- 默写待默数按"本次背诵是否已有对应默写"计算，重背旧词也会重新进入默写
- 跨天不再把上一组旧词滚进今日目标

### 新增
- 逐次背默事件：`readEventId`、`page`、`ts`、`sessionId`；默写事件带 `readEventId`、`readAt`、`score`
- 错题事件记录来源（背诵事件或默写事件）
- 每日清零墓碑 `dailyReset` 与逐词清零墓碑 `progResetAt` / `passClearAt`，防止旧设备把清零前的记录合并回来
- 用户指定基线：第 1~7 页可标记为"全部背过 / 全部已默"，带 `readBaselineNote` / `writeBaselineNote`，不伪造逐次事件

### 已知限制
- 云同步为单份快照覆盖，没有历史版本
- 原始 PDF / CSV 不入仓库，仅保留解析后的词库
