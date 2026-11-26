#!/bin/bash
# 词迹 Git 初始化和推送脚本
# 使用前请先确定要推送到哪个平台（GitHub/Gitee/GitLab 等）

set -e

PROJECT_DIR="/d/VocabLab"
cd "$PROJECT_DIR"

# 1. 初始化 Git 仓库
if [ ! -d ".git" ]; then
  echo "[1/4] 初始化 Git 仓库..."
  git init
else
  echo "[1/4] Git 仓库已存在，跳过初始化"
fi

# 2. 添加所有文件
echo "[2/4] 添加文件到暂存区..."
git add .

# 3. 创建首次提交
echo "[3/4] 创建首次提交..."
git commit -m "初始提交：词迹 v1.0.0

- 桌面端 Electron 应用
- 安卓端 APK（WebView 壳）
- 云同步（WorkBuddy Cloud Service）
- 背诵/默写分开、错词本复习
- AI 配色、天气时令、今日进度
- 鸣谢：柳重名神"
else
  echo "[3/4] 已有提交，跳过"
fi

# 4. 添加远程仓库（请根据平台选择）
echo "[4/4] 添加远程仓库..."
echo "请选择要推送到哪个平台："
echo "  1) GitHub"
echo "  2) Gitee（码云）"
echo "  3) GitLab"
echo "  4) 自定义 URL"
read -p "请选择 (1-4): " choice

case $choice in
  1)
    read -p "请输入 GitHub 仓库 URL（https://github.com/用户名/仓库名.git）: " repo_url
    git remote add origin "$repo_url"
    ;;
  2)
    read -p "请输入 Gitee 仓库 URL（https://gitee.com/用户名/仓库名.git）: " repo_url
    git remote add origin "$repo_url"
    ;;
  3)
    read -p "请输入 GitLab 仓库 URL: " repo_url
    git remote add origin "$repo_url"
    ;;
  4)
    read -p "请输入自定义远程仓库 URL: " repo_url
    git remote add origin "$repo_url"
    ;;
  *)
    echo "未选择平台，跳过添加远程仓库"
    exit 0
    ;;
esac

# 5. 推送到远程
echo ""
echo "正在推送到 $choice ..."
git branch -M main
git push -u origin main

echo ""
echo "✓ 推送完成！"
echo "仓库地址：$repo_url"
