#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import struct
import io
from PIL import Image

def svg_to_ico(svg_path, ico_path):
    # 读取 SVG
    with open(svg_path, 'r', encoding='utf-8') as f:
        svg_content = f.read()

    # 创建多个尺寸的 PNG
    sizes = [32, 48, 64, 128, 256]
    images = []

    # 使用临时文件
    temp_files = []
    try:
        for size in sizes:
            # 创建临时 PNG 文件
            temp_path = f'_temp_{size}.png'
            with open(temp_path, 'wb') as f:
                f.write(svg_content.encode('utf-8'))

            # 用 PIL 读取并调整大小
            img = Image.open(io.BytesIO(svg_content.encode('utf-8')))
            img = img.resize((size, size), Image.Resampling.LANCZOS)
            img.save(temp_path, 'PNG')

            # 读取回内存
            with open(temp_path, 'rb') as f:
                buffer = f.read()

            images.append((size, buffer))
            temp_files.append(temp_path)

        # 合成 ICO
        ico_data = bytearray()

        # ICO 头
        ico_data.extend(struct.pack('<HH', 0, 1))  # Reserved, Type
        ico_data.extend(struct.pack('<H', len(images)))  # Count

        # 图标目录项
        for size, buffer in images:
            # ICO 目录项（简化版）
            ico_data.extend(struct.pack('<BBHHH', size, size, 0, 1, 32))  # Width, Height, Colors, Reserved, Planes, BitsPerPixel
            ico_data.extend(struct.pack('<I', len(buffer)))  # Size
            ico_data.extend(struct.pack('<I', 6 + len(images) * 16))  # Offset

        # 图标图像数据
        for size, buffer in images:
            ico_data.extend(buffer)

        # 写入 ICO 文件
        with open(ico_path, 'wb') as f:
            f.write(ico_data)

        print(f'ICO 生成完成: {ico_path}')
        print(f'包含尺寸: {", ".join(str(s) for s in sizes)}')

    finally:
        # 清理临时文件
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)

if __name__ == '__main__':
    svg_to_ico('vocab.svg', 'icon.ico')
