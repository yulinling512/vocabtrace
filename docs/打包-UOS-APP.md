# 词迹 - 打包成 UOS APP

## 目标

将 Electron 项目打包成 UOS 能直接安装的应用：

- **UOS 上安装**：双击 `.deb` 或 `.AppImage` 即可
- **无需 Node.js**：安装后直接用，不依赖开发环境
- **跨平台**：打包一次，Windows/macOS/Linux 都能用

## 一、打包成 AppImage（推荐）

AppImage 是 Linux 通用格式，UOS 直接双击就能运行。

### 步骤 1：安装 electron-builder

```bash
cd /d/VocabLab/源码/desktop
npm install electron-builder --save-dev
```

### 步骤 2：修改 package.json

在 `package.json` 中添加以下配置：

```json
{
  "name": "vocab-trace",
  "productName": "词迹",
  "version": "1.0.0",
  "description": "认读型背词工具",
  "main": "main.js",
  "scripts": {
    "start": "electron .",
    "pack": "electron-builder --dir",
    "build": "electron-builder",
    "build:linux": "electron-builder --linux"
  },
  "build": {
    "appId": "com.vocabtrace.app",
    "productName": "词迹",
    "directories": {
      "output": "dist"
    },
    "files": [
      "index.html",
      "seed.js",
      "main.js",
      "node_modules/**/*",
      "assets/**/*"
    ],
    "win": {
      "target": [
        {
          "target": "nsis",
          "arch": ["x64"]
        }
      ]
    },
    "linux": {
      "target": [
        {
          "target": "appimage",
          "arch": ["x64"]
        }
      ],
      "category": "Education",
      "icon": "vocab.svg"
    },
    "mac": {
      "target": [
        {
          "target": "dmg",
          "arch": ["x64"]
        }
      ]
    }
  }
}
```

### 步骤 3：打包成 AppImage

```bash
npm run build:linux
```

产物位置：`源码/desktop/dist/词迹-1.0.0.AppImage`

### 步骤 4：在 UOS 上安装

1. 将 `词迹-1.0.0.AppImage` 传输到 UOS 机器
2. 双击运行，会提示「是否允许运行此应用？」
3. 勾选「一律允许」，应用就会安装到系统菜单

## 二、打包成 .deb 包

`.deb` 是 Debian 系系统（UOS 基于 Debian）的原生包格式。

### 步骤 1：安装 electron-builder

```bash
cd /d/VocabLab/源码/desktop
npm install electron-builder --save-dev
```

### 步骤 2：修改 package.json

在 `package.json` 中添加以下配置：

```json
{
  "build": {
    "appId": "com.vocabtrace.app",
    "productName": "词迹",
    "directories": {
      "output": "dist"
    },
    "files": [
      "index.html",
      "seed.js",
      "main.js",
      "node_modules/**/*",
      "assets/**/*"
    ],
    "linux": {
      "target": [
        {
          "target": "deb",
          "arch": ["x64"]
        }
      ],
      "category": "Education",
      "icon": "vocab.svg"
    }
  }
}
```

### 步骤 3：打包成 .deb

```bash
npm run build:linux
```

产物位置：`源码/desktop/dist/词迹_1.0.0_amd64.deb`

### 步骤 4：在 UOS 上安装

1. 将 `词迹_1.0.0_amd64.deb` 传输到 UOS 机器
2. 右键 → 打开方式 → 安装包安装
3. 或在终端执行：
   ```bash
   sudo dpkg -i 词迹_1.0.0_amd64.deb
   ```

## 三、打包成 Windows 安装包（可选）

如果你在 Windows 上打包，可以生成 Windows 安装包：

```bash
npm run build
```

产物位置：`源码/desktop/dist/词迹-1.0.0 Setup.exe`

## 四、打包后测试

### 在当前机器测试 AppImage

```bash
cd 源码/desktop/dist
chmod +x 词迹-1.0.0.AppImage
./词迹-1.0.0.AppImage
```

### 在 UOS 上测试

1. 将 `词迹-1.0.0.AppImage` 传输到 UOS
2. 双击运行
3. 首次启动会自动铺好 601 词词库
4. 使用邮箱 + 密码登录，自动从云端同步

## 五、常见问题

### 1. 打包失败：找不到 icon.svg

**原因**：electron-builder 默认需要 `.png` 或 `.ico` 格式图标

**解决**：
- 保留 `vocab.svg` 作为源文件
- electron-builder 会自动转换

### 2. 打包后体积太大

**原因**：`node_modules` 打进去了

**解决**：在 `package.json` 的 `files` 中排除不需要的依赖：

```json
"files": [
  "index.html",
  "seed.js",
  "main.js",
  "assets/**/*",
  "node_modules/electron/**/*",
  "node_modules/electron-builder/**/*"
]
```

### 3. UOS 上双击 AppImage 提示「没有执行权限」

**解决**：
```bash
chmod +x 词迹-1.0.0.AppImage
```

### 4. UOS 上提示「缺少依赖库」

**解决**：UOS 自带必要的 GTK、NSS 等库，如仍报错，安装：

```bash
sudo apt-get install -y libgtk-3-0 libnotify4 libnss3 libxss1 libasound2
```

## 六、更新打包流程

修改代码后重新打包：

```bash
cd 源码/desktop

# 清理旧的构建文件
rm -rf dist node_modules/.cache

# 重新打包
npm run build:linux
```

## 七、分发

打包完成后，你可以：

1. **自己安装使用**：直接在 UOS 上安装测试
2. **分享给别人**：通过邮件、U 盘、网盘发送 `.deb` 或 `.AppImage`
3. **上传到应用商店**：如果 UOS 有应用商店，可以提交审核

---

**鸣谢**：由 **柳重名神** 创作
