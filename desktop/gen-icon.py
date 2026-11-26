# -*- coding: utf-8 -*-
"""生成「词迹」应用图标：墨绿渐变底 + 居中「词」字，克制、正式。

产物：icon.ico（16–256 多尺寸）、preview.png、preview-32.png
用法：python gen-icon.py
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
S = 4                     # 超采样
N = 256
W = N * S

TOP = (42, 104, 75)       # #2A684B 顶部
BOT = (18, 58, 42)        # #123A2A 底部
INK = (251, 247, 236)     # 米白 #FBF7EC
FONT = "C:/Windows/Fonts/msyhbd.ttc"

# ---------- 底：垂直渐变 ----------
base = Image.new("RGBA", (W, W))
d = ImageDraw.Draw(base)
for y in range(W):
    t = y / (W - 1)
    c = tuple(int(BOT[i] + (TOP[i] - BOT[i]) * (1 - t)) for i in range(3))
    d.line([(0, y), (W, y)], fill=c + (255,))

# 顶部柔光：小白点大范围模糊，只在上半部分
halo = Image.new("RGBA", (W, W), (0, 0, 0, 0))
ImageDraw.Draw(halo).ellipse([-W * 0.15, -W * 1.05, W * 1.15, W * 0.30], fill=(255, 255, 255, 20))
halo = halo.filter(ImageFilter.GaussianBlur(W // 10))
base = Image.alpha_composite(base, halo)

# 圆角遮罩
mask = Image.new("L", (W, W), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, W - 1, W - 1], radius=int(W * 0.226), fill=255)
base.putalpha(mask)

# 内描边：一圈 1px 亮边，浅色桌面上不糊边
edge = Image.new("RGBA", (W, W), (0, 0, 0, 0))
ImageDraw.Draw(edge).rounded_rectangle(
    [S, S, W - S, W - S], radius=int(W * 0.222), outline=(255, 255, 255, 36), width=max(1, S)
)
base = Image.alpha_composite(base, edge)
base.putalpha(Image.composite(base.getchannel("A"), Image.new("L", (W, W), 0), mask))

# ---------- 「词」 ----------
font = ImageFont.truetype(FONT, int(N * 0.505 * S), index=0)
bbox = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), "词", font=font)
tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
tx = (W - tw) / 2 - bbox[0]
ty = (W - th) / 2 - bbox[1] - W * 0.012      # 光学居中，略上提

sh = Image.new("RGBA", (W, W), (0, 0, 0, 0))
ImageDraw.Draw(sh).text((tx, ty + W * 0.012), "词", font=font, fill=(0, 0, 0, 72))
sh = sh.filter(ImageFilter.GaussianBlur(W * 0.013))
base = Image.alpha_composite(base, sh)

d = ImageDraw.Draw(base)
d.text((tx, ty), "词", font=font, fill=INK + (255,))

# ---------- 输出 ----------
big = base.resize((N, N), Image.LANCZOS)
big.save(os.path.join(HERE, "preview.png"))
big.resize((32, 32), Image.LANCZOS).resize((128, 128), Image.NEAREST).save(os.path.join(HERE, "preview-32.png"))

big.save(
    os.path.join(HERE, "icon.ico"),
    format="ICO",
    sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (24, 24), (16, 16)],
)
print("icon.ico / preview.png 已生成")

# Linux 打包（electron-builder 的 AppImage/deb target）要求 512x512 的 PNG。
# 底图是矢量生成的，放大到 512 不会有锯齿问题。
big.resize((512, 512), Image.LANCZOS).save(os.path.join(HERE, "icon-512.png"), format="PNG")
print("icon-512.png 已生成")
