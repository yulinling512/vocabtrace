# 词迹 (VocabTrace)

**认读型背单词工具，支持云端同步、AI 配色、背默分开、错词本复习。**

## 功能

- 📚 **背诵 + 默写分开**：同一次背默分开标记，可重新再背/再默
- 📱 **多端同步**：电脑 + 手机 + 云端进度实时同步
- 🎨 **AI 配色**：根据日期、节气、天气自动配一套配色
- 📊 **今日进度**：首页直观显示今日学词、错词、累计进度
- 🔍 **错词本**：按背诵/默写分别复习，支持完整释义和再背一轮
- 🌤️ **天气时令**：根据所在城市显示天气、节气、季节
- 📖 **词源和记法**：AI 生成词源、速记、记忆策略
- 🎯 **每组词数可调**：20/36/50/100 或自定义，随书调整
- ⌨️ **快捷键**：背诵/默写切换、翻面、跳过、判分（桌面端）

## 系统要求

### 桌面端（Electron）

- Node.js >= 16
- npm 或 yarn
- Linux/Windows/macOS

### 安卓端（APK）

- 安卓 5.0+（API 19+）
- 安卓 SDK 34
- 构建环境：JDK 17、Android SDK command-line tools、build-tools 34.0.0

## 安装与运行

### 桌面端

```bash
cd 源码/desktop
npm install
npm start
```

### 安卓端

```bash
cd 源码/desktop
npm install
node build.js  # 生成 APK
```

APK 产物：`安装包/词迹-安卓-1.0.0.apk`

### 统信 UOS 部署

统信 UOS 基于 Debian，和普通 Linux 桌面一样，直接安装依赖即可：

```bash
# 安装 Node.js（推荐 16+）
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo bash -
sudo apt-get install -y nodejs

# 安装 Electron 依赖
sudo apt-get install -y libgtk-3-0 libnotify4 libnss3 libxss1 libasound2

# 克隆项目并运行
git clone <your-repo-url>
cd vocab-trace/源码/desktop
npm install
npm start
```

打包成 `.deb` 或 `.AppImage`：

```bash
npm run pack  # 打包成 AppImage
npm run setup  # 打包成 Windows 安装包（需要 Windows）
```

## 使用说明

详细使用说明见：`使用说明.txt`

## 开发说明

- **桌面端**：Electron 单页应用，主界面 `index.html`，逻辑在 `<script>` 中。
- **安卓端**：最小原生 WebView 壳，页面嵌入 assets，通过 JS Bridge 交互。
- **云同步**：WorkBuddy Cloud Service（`vocab-trace.app.workbuddy.host`），SDK 内联。
- **存档**：本地 `数据/账号/<uid>.json`，每日自动备份。

## 词序与页码（2026-11-26 修正）

词库 601 词按《高频词默写》（扫描件 17 页）的**真题频次顺序**排列，每个词带 `pg`（页码），
每页 36 个（末页 25 个），与应用里「一天一页」的分组严格对应：

- 取词逻辑按 `pg` 分页，取「第一个还没全默过的页」，页内打乱、页序推进（`pageGroups()`）。
- 纸质默写纸第 N 页 = 应用第 N 页；`词库/高频词默写.csv` 也按同一顺序。
- 历史坑：早期版本词库是字母序，纸质是频次序，两边同页不同词。
  修正前的 216 条假进度（把「字母序前 6 页」当纸质前 6 页）由 `applyCut()` 按时间水位清掉，
  水位常量 `PASS_FLOOR = 1795623020207`（2026-11-26 00:10:20），早于它的 pass 一律不认。

## 许可证

MIT

## 鸣谢

由 **柳重名神** 创作

## 界面改版（2026-11-26 晚）

- **图标**：重画为「深靛渐变圆角方 + 象牙白打开的书 + 琥珀书签」，输出 `icon.ico`(16–256)、`icon-512.png`、`图标\词迹.ico`、安卓 mipmap 五档密度（mdpi→xxxhdpi）。
- **主色**：默认主题由苔绿 `#1F6B4F` 改为靛青 `#2B5C8E`（深色主题对应 `#86B4DC`）；顶栏「词迹」左边的方块改用书本字形，头像由圆角方形改为圆形并带描边。
- **错词本配色**：色盘把第三支转成绿色，与靛青打架，单独钉成琥珀 `#BF8339`（深色 `#D2A05C`）；首页卡片顶部渐变色带改为蓝→靛，不再带绿。
- **动效**：视图子元素依次浮现（45ms 递进）、卡片悬停微浮起、进度条 0.55s 长出、翻卡改为 62° 轻翻、默写判错时词面抖动（nudge）/判对轻顶（tick）。
- **账号显示**：新增 `displayName()`（昵称 → 账号名 → 邮箱前缀 → 「你」），顶栏与设置页同源；云端账号不再落到「我」，并支持换头像（192px JPEG 存进 `cfg.av`，随快照同步）。
- **产物**：`词迹-安卓-1.0.2.apk`（versionCode 3，同钥匙可覆盖升级）、`词迹-1.0.2-amd64.deb`；Windows 侧 `程序\词迹.exe` 已用 rcedit 换图标，桌面快捷方式指向 `图标\词迹.ico`。

## 界面改版 v2（2026-11-26 21:00 · 1.0.3）

- **图标转橙**：渐变 `#F29A45 → #D0641E`，书页象牙白，书签改深墨 `#203040`（32px 小尺寸最清楚）；同步输出 ico(16–256)、512 png、安卓五档 mipmap。exe 内嵌图标已用 rcedit 重刷（必须先把 exe 和 ico 复制到纯 ASCII 路径 `C:\rctest`，中文路径会 load 失败）。
- **头像改回圆角方**：顶栏 27px / 圆角 9px，设置页 48px / 圆角 16px，橙色渐变 + 白字；不再用圆形。
- **主色去掉绿色**：默认主色改暖橙 `#B96A22`（深色 `#E9A468`）；色盘 accent2 色相只偏 +10、sat .94，accent3 偏 −16，accent4 取反差 168 但饱和度压到 .42 —— 四张功能卡是同一盒彩铅的四种色，不再转出苔绿。
- **配色交还 AI**：首次进站若已填 key 且主题是 ai，静默自动请求一次 `aiPaletteBase()`（日期/节气/季节/时段/天气/头像色/最近在背的词 → JSON 调色板）；失败不弹提示。AI 给的色仍会走 `seasonalBase()` 做节气微调。
- **窗口圆角**：`BrowserWindow` 改 `transparent:true` + `backgroundColor:'#00000000'`，body `border-radius:16px` + 内描边；最大化/全屏时打 `.maxed` 去掉圆角。因为 `overflow:hidden` 会废掉文档滚动，滚动整体搬进 `main`（注意 `main` 必须 `width:100%`，否则会被 flex 压到 447px）。
- **字符装饰层**：`.deco` 绝对定位层（`pointer-events:none`），内含等宽字体二进制列、`{trace}` 代码块、底部 `00 01 10 11`、三团水彩晕、散布的 0/1/@/#/+ 单字、右侧「打孔纸卡」ASCII 小卡。全部低透明度，只做纸面纹理。
- **致敬区**：从设置页中部移到最底，扩为 8 行（版本/词库/词源/判分/配色/数据/底本/鸣谢）+ 等宽小字页脚。
- **产物**：`词迹-安卓-1.0.3.apk`（versionCode 4，同钥匙可覆盖升级，SHA-256 `dcee3057…`）、`词迹-1.0.3-amd64.deb`。

