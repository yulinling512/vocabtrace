#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成「词迹」应用图标 B 方案：白底书本 + 橙色 WORD 卡片。

精确复刻 vocab.svg 的几何设计（viewBox 0 0 64 64），用 PIL 直接
按矢量坐标绘制，1024 超采样后缩到各尺寸，小图标依然清晰。

产物（覆盖旧文件，旧的已备份到 .backup-* 目录）：
  icon.ico       Windows 快捷方式 / NSIS（16-256 多尺寸）
  icon-512.png   Linux deb / AppImage 桌面图标
  preview.png    预览
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
S = 1024                       # 画布尺寸（64 viewBox 的 16 倍）
K = S / 64.0

# vocab.svg 原配色
DARK = (44, 62, 80, 255)       # #2C3E50 书本描边
PAPER = (248, 249, 250, 255)   # #F8F9FA 书页
SHADE = (233, 236, 239, 255)   # #E9ECEF 书脊阴影
ORANGE = (255, 140, 66, 255)   # #FF8C42 卡片描边
CARD = (255, 245, 240, 255)    # #FFF5F0 卡片底
CLEAR = (0, 0, 0, 0)


def px(v):
    return v * K


def main():
    img = Image.new('RGBA', (S, S), CLEAR)
    d = ImageDraw.Draw(img)
    lw = lambda w: max(1, round(w * K))

    # 书本：圆角矩形（原 SVG 用 linecap=round 的四段线，等价于圆角矩形）
    d.rounded_rectangle([px(12), px(16), px(52), px(48)],
                        radius=px(1.5), fill=PAPER,
                        outline=DARK, width=lw(2.5))
    # 书脊阴影（先画在左，中缝覆盖其上）
    d.line([px(31), px(17), px(31), px(47)], fill=SHADE, width=lw(1.5))
    # 中缝
    d.line([px(32), px(16), px(32), px(48)], fill=DARK, width=lw(1.5))
    # 单词卡片
    d.rounded_rectangle([px(38), px(22), px(54), px(42)],
                        radius=px(3), fill=CARD,
                        outline=ORANGE, width=lw(2))
    # 笔：斜杆 + 笔尖
    d.line([px(46), px(22), px(52), px(16)], fill=DARK, width=lw(2))
    d.rounded_rectangle([px(50), px(16), px(52), px(22)],
                        radius=px(1), fill=DARK)

    # 卡片上的 WORD 字样：按原设计尺寸（8/64），允许超出卡片与书本边缘；
    # 颜色用深蓝墨色 —— 与米白卡底、白色书页都拉开对比，且区别于橙色描边
    font = None
    for name in ('arialbd.ttf', 'arial.ttf', 'seguisb.ttf', 'segoeui.ttf',
                 'DejaVuSans-Bold.ttf', 'DejaVuSans.ttf'):
        try:
            font = ImageFont.truetype(name, int(px(8)))
            break
        except Exception:
            continue
    if font is not None:
        txt = 'WORD'
        bbox = d.textbbox((0, 0), txt, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        cx, cy = px(46), px(33.5)
        d.text((cx - tw / 2 - bbox[0], cy - th / 2 - bbox[1]),
               txt, font=font, fill=DARK)
    else:
        print('  ⚠ 未找到可用字体，WORD 字样省略')

    # 输出
    ico_sizes = [16, 24, 32, 48, 64, 128, 256]
    frames = [img.resize((s, s), Image.Resampling.LANCZOS) for s in ico_sizes]
    frames[-1].save(os.path.join(HERE, 'icon.ico'), 'ICO',
                    sizes=[(s, s) for s in ico_sizes])
    img.resize((512, 512), Image.Resampling.LANCZOS).save(
        os.path.join(HERE, 'icon-512.png'), 'PNG')
    img.resize((256, 256), Image.Resampling.LANCZOS).save(
        os.path.join(HERE, 'preview.png'), 'PNG')

    # 安卓 xxxhdpi 启动图标（192x192）
    android_res = os.path.join(HERE, '..', '..', 'android', 'res',
                               'mipmap-xxxhdpi', 'ic_launcher.png')
    if os.path.isdir(os.path.dirname(android_res)):
        img.resize((192, 192), Image.Resampling.LANCZOS).save(android_res, 'PNG')
        print('✓ 安卓图标已更新：' + android_res)

    print('✓ icon.ico / icon-512.png / preview.png 已更新为 B 方案')


if __name__ == '__main__':
    main()
