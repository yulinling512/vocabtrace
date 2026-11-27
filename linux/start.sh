#!/bin/bash
# 词迹 1.1.0 · Linux ARM64 便携版启动脚本
cd "$(dirname "$0")/程序" || exit 1
exec ./vocab-trace --no-sandbox "$@"
