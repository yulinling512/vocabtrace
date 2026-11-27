# 词迹 · VocabTrace

> 看英文，想中文。一个「认读型」背单词应用：给英文，想中文意思，不考拼写。

词迹是为中文母语者做的英语词汇训练工具。它不追求"背了多少个"，而是让你在**看到英文的瞬间反应出中文含义**——这是阅读和听力真正需要的能力。

当前版本：**1.1.0**（Windows / Linux），Android 为 **1.1.1**（versionCode 118）

## 它做什么

- **背诵（认读）**：屏幕给出英文单词，你心里想出中文，翻面对答案，自评"记住 / 没记住"
- **默写（拼写）**：给中文或释义，写出英文，逐字判分
- **查词**：内置本地英汉词典，查词出卡片；桌面端优先读本地 ECDICT 精简索引，未命中再走 AI
- **生词本**：查过、背错、默错的词自动收录，按时间与使用情况排序
- **错词本**：背错或默错的词自动进入，背、默两侧各有一份"复习过"标记，两侧都过了才算真正划掉
- **书架**：可导入多本书，各自独立进度，互不干扰
- **进度与云同步**：桌面端把进度写成硬盘上的一个文件，换机器拷走即可；也支持登录云端账号跨设备合并

## 1.1.x 的关键改动

- **查词层**：新增 `lookup` 视图、本地词典接口 `/api/dict`、查词卡片与骨架屏；卡片样式统一
- **新视图**：生词本 `notebook`、新闻 `news`、训练 `train`、报告 `report`、句子 `sentence`、历史 `history`
- **桌面主进程**：新增 `/api/news`；数据目录按"程序同级 `数据`"优先，装到只读目录时自动退回用户配置目录
- **安卓端**：内置精简词典 `assets/dict.js`（约 3.3 MB），离线可查；包体从 0.5 MB 增至 1.7 MB
- **Linux 端**：新增 ARM64 构建脚本与便携包，适配麒麟 990 / 统信 UOS

## 设计上的几个坚持

- **取词顺序按真题出现频次**，不是字母序。先背最可能考的。
- **判分在本地完成**，字面规则打底，拿不准的才交给 AI 复核，离线也能用。
- **配色交给 AI 生成**：按节气、天气、季节和你最近在背的词，每天换一套色板，不用你手动挑。
- **界面是一张纸**：线描莲花、书页框、朱印、编号卡片、代码底纹——不做成常见的"卡片 + 渐变按钮"。

## 下载

到 Releases 取安装包（最新为 `v1.1.1` 一版多附件）：

- Windows：`vocabtrace-win-1.1.0-portable.zip`，解压即用，含本地词典
- 安卓：`vocabtrace-android-1.1.1.apk`，直接安装
- Linux ARM64：`vocabtrace-linux-arm64-1.1.0.tar.gz`，解压后 `./start.sh`；旧的 amd64 deb 仍在历史 Release
- 源码：`vocabtrace-source-1.1.1.zip`

## 目录

```
app/index.html              界面全部（单文件 HTML，无构建依赖）
android/                    安卓工程（WebView 壳 + 原生资源 + build-apk.ps1）
desktop/                    桌面端外壳：主进程、打包脚本、图标生成
linux/                      Linux ARM64 便携包脚本与说明
schema/  spec/              词库结构定义、导入格式与 AI 出题提示词
data/                       词库（601 词，含释义、词源、例句、搭配）
_cards/  _etym/  _tips/     分词卡的原始文本批次
tools/                      辅助脚本（快捷方式、PDF 抽页）
docs/                       打包、部署与使用说明
icons/                      应用图标
```

## 从源码构建

```bash
# 桌面端（Electron 33.4.11）
cd desktop && npm install && npm run build

# 安卓（需 JDK 17 + Android SDK build-tools 34）
cd android && ./build-apk.ps1 -Ver 1.1.1 -Code 118
```

安卓打包需要自己的签名证书；仓库**不包含** keystore。

## 云端同步配置

`app/index.html` 顶部的 `CLOUD_CFG` 是云同步入口：

```js
const CLOUD_CFG = {
  endpoint: 'https://<your-project>.app.workbuddy.host',
  oauthRelayBaseUrl: 'https://www.workbuddy.cn/v2/as/genie-baas/oauth',
  publishableKey: ''   // 填入你自己的 publishableKey
};
```

`publishableKey` 留空时应用完全离线可用，只是没有跨设备同步。填入后，登录账号即可上传/拉取整包存档。

## 不包含什么

这个仓库**不含**：个人学习进度存档、云端 API 密钥、AI 服务密钥、签名证书，以及 exe / deb / apk 这类打包产物（大件走 Release 附件）。授权信息在运行时由使用者自己填写。

## 授权

界面与词库由作者整理。如需转载或二次分发，请先联系作者。
