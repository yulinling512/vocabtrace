# 词迹 - 统信 UOS 部署指南

## 一、系统要求

- **操作系统**：统信 UOS 20（桌面版）或麒麟 V10
- **架构**：x86_64（华为擎云笔记本通常是 x86_64）
- **可用内存**：至少 4GB
- **磁盘空间**：至少 2GB 可用空间

## 二、安装 Node.js

### 方法 1：通过 UOS 软件商店（推荐）

1. 打开「软件商店」
2. 搜索「Node.js」或「Node.js 16/18」
3. 选择 LTS 版本安装（推荐 18.x）
4. 安装完成后，在终端运行 `node -v` 确认版本

### 方法 2：通过官网下载

1. 访问 https://nodejs.org/
2. 下载 LTS 版本（例如：node-v18.x-linux-x64.tar.xz）
3. 解压到 `/opt/nodejs`：
   ```bash
   sudo tar -xJf node-v18.x-linux-x64.tar.xz -C /opt/
   ```
4. 添加到 PATH：
   ```bash
   echo 'export PATH=/opt/nodejs/node-v18.x-linux-x64/bin:$PATH' >> ~/.bashrc
   source ~/.bashrc
   ```
5. 运行 `node -v` 确认安装成功

## 三、安装 Electron 依赖

在终端中执行：

```bash
# 安装 GTK3、通知、NSS、XSS、音频等依赖
sudo apt-get update
sudo apt-get install -y \
  libgtk-3-0 \
  libnotify4 \
  libnss3 \
  libxss1 \
  libasound2 \
  libxtst6 \
  libatspi2.0-0 \
  libcups2 \
  libdrm2 \
  libxkbcommon0 \
  libxcomposite1 \
  libxdamage1 \
  libxfixes3 \
  libxrandr2 \
  libgbm1 \
  libpango-1.0-0 \
  libcairo2 \
  libgdk-pixbuf2.0-0
```

## 四、获取词迹项目

### 方法 1：克隆 Git 仓库（推荐）

```bash
# 安装 Git
sudo apt-get install -y git

# 克隆项目
git clone https://github.com/你的用户名/词迹仓库.git
cd 词迹仓库
```

### 方法 2：手动下载

1. 从 GitHub/Gitee 下载 ZIP 包
2. 解压到 `/opt/词迹`
3. 进入目录：`cd /opt/词迹`

## 五、安装依赖并运行

```bash
# 进入项目目录
cd /opt/词迹/源码/desktop

# 安装 Node.js 依赖
npm install

# 启动应用
npm start
```

### 首次运行

1. 应用会自动打开浏览器窗口
2. 首次启动会自动铺好 601 词词库
3. 使用邮箱 + 密码登录（首次需要先在登录页点击「忘记密码？」设密码）
4. 登录后会自动从云端同步进度和错词本

## 六、打包成独立应用（可选）

如果你想打包成 `.deb` 或 `.AppImage`，方便分享：

```bash
cd /opt/词迹/源码/desktop

# 打包成 AppImage（Linux）
npm run pack

# 打包成 Windows 安装包（需要 Windows 环境）
npm run setup
```

产物位置：
- AppImage：`源码/desktop/dist/词迹-1.0.0.AppImage`
- Windows 安装包：`源码/desktop/dist/词迹-1.0.0 Setup.exe`

## 七、常见问题

### 1. 启动后窗口不显示

**原因**：缺少 GTK 或其他图形库依赖

**解决**：
```bash
sudo apt-get install -y libgtk-3-0 libnotify4 libnss3 libxss1 libasound2
```

### 2. 启动后黑屏或白屏

**原因**：Electron 版本与系统不兼容

**解决**：
```bash
cd /opt/词迹/源码/desktop
rm -rf node_modules package-lock.json
npm install
npm start
```

### 3. 网络请求失败（云端同步）

**原因**：系统代理或防火墙拦截

**解决**：
- 检查网络连接
- 如需代理，在终端设置环境变量：
  ```bash
  export HTTP_PROXY=http://127.0.0.1:7890
  export HTTPS_PROXY=http://127.0.0.1:7890
  npm start
  ```

### 4. 没有菜单栏或任务栏

**原因**：Electron 应用配置问题

**解决**：检查 `main.js` 中是否有 `titleBarStyle: 'hidden'` 或 `backgroundColor: '#fff'`，如有则删除或注释。

### 5. 按键快捷键失效

**原因**：系统输入法冲突

**解决**：
- 在设置中关闭「快捷键」功能
- 或在终端中设置 `ELECTRON_DISABLE_SANDBOX=1` 运行

## 八、更新应用

```bash
cd /opt/词迹/源码/desktop

# 拉取最新代码
git pull

# 重新安装依赖
rm -rf node_modules package-lock.json
npm install

# 重启应用
npm start
```

## 九、卸载

```bash
# 停止应用（如果在运行）
pkill 词迹

# 删除项目目录
sudo rm -rf /opt/词迹

# 如需卸载 Node.js，请参考 Node.js 官方文档
```

## 十、联系与反馈

如有问题，可通过以下方式联系：

- GitHub Issues：https://github.com/你的用户名/词迹仓库/issues
- 鸣谢：由 **柳重名神** 创作
