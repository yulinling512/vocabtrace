#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""纯 Python 的 SquashFS 4.0 写入器 —— 用于在 Windows 上打 AppImage。

背景：AppImage = ELF runtime + squashfs 镜像。官方 mksquashfs 只有
Linux/macOS 版，electron-builder 在 Windows 上打 AppImage 会去找
Linux 的 mksquashfs，直接 ENOENT。本脚本用 Python 补齐这一步。

实现要点（squashfs 4.0，小端）：
  * 元数据（inode 表/目录表）按 8192 字节切块、不压缩存储
    （块头 u16 置 0x8000 表示未压缩）→ 所有偏移写入前即确定，
    规避"引用值依赖压缩后大小"的循环依赖。
  * 数据块逐块 zlib 压缩；inode 的 block list 记录压缩后长度，
    未压缩块需置 0x01000000 标志位（bit 置位 = 未压缩）。
  * 普通文件 inode 的 start_block 是数据块在镜像内的绝对偏移。
  * 目录项表按子 inode 所在 metadata 块分组，每组一个 DirHeader
    （start_block = 组内子项在 inode 表内的字节偏移，全组共享）。
  * 不用 fragment / 导出表 / xattr（相应字段填 INVALID）。

用法：python squashfs-writer.py <源目录> <输出文件> [--validate]
"""
import os
import struct
import sys
import time
import zlib

SQUASHFS_MAGIC = 0x73717368
METADATA_SIZE = 8192
BLOCK_LOG = 17
BLOCK_SIZE = 1 << BLOCK_LOG
COMPRESSION_ZLIB = 1
META_UNCOMPRESSED = 0x8000
DATA_UNCOMPRESSED = 0x01000000

INODE_DIR, INODE_REG, INODE_SYMLINK = 1, 2, 3
TYPE_DIR, TYPE_REG, TYPE_SYMLINK = 1, 2, 3
INVALID_FRAG = 0xFFFFFFFF
INVALID_BLK64 = 0xFFFFFFFFFFFFFFFF

# Windows 的 stat 不带可执行位（一律 666），上 Linux 会直接起不来。
# 这里按文件名显式指定可执行权限，其余一律 644。
EXEC_MODES = {
    'AppRun': 0o755,
    'vocab-trace': 0o755,
    'chrome_crashpad_handler': 0o755,
    'chrome-sandbox': 0o4755,      # Electron SUID 沙箱
}


def disk_mode(node):
    if node.kind == 'dir':
        return 0o755
    if node.kind == 'link':
        return 0o777
    return EXEC_MODES.get(node.name, 0o644)


class Node:
    def __init__(self, path, name, kind):
        self.path = path
        self.name = name
        self.kind = kind            # 'dir' / 'file' / 'link'
        self.stat = None
        self.children = []
        self.inode_number = 0
        self.inode_ref = 0          # mkinode 编码后的 u64
        self.inode_blk_index = 0    # inode 记录所在的 metadata 块号
        self.inode_blk_off = 0      # 在 metadata 块内的内容偏移
        self.inode_hdr_off = 0      # 所在块头的表内磁盘偏移
        self.data_abs = 0           # 首个数据块的镜像绝对偏移
        self.block_sizes = []       # 数据块记录（含未压缩标志位）
        self.file_size = 0


def scan_tree(root):
    """扫描目录树，返回 (根节点, 全部节点列表)。"""
    nodes = []
    counter = [0]

    def walk(path, name, kind):
        full = os.path.join(path, name) if path else name
        st = os.lstat(full)
        node = Node(full, name, kind)
        node.stat = st
        counter[0] += 1
        node.inode_number = counter[0]
        nodes.append(node)
        if kind == 'dir':
            for entry in sorted(os.listdir(full)):
                child_path = os.path.join(full, entry)
                if os.path.islink(child_path):
                    child = walk(full, entry, 'link')
                elif os.path.isdir(child_path):
                    child = walk(full, entry, 'dir')
                elif os.path.isfile(child_path):
                    child = walk(full, entry, 'file')
                else:
                    continue
                node.children.append(child)
        return node

    return walk(root, '', 'dir'), nodes


class MetaTable:
    """未压缩元数据表：顺序写入，每 8192 字节切一块。

    磁盘布局：每块 = 2 字节头 + 8192 字节内容，连续存放。
    因此第 k 块头的表内偏移 = k * (8192 + 2)，不是 k * 8192 ——
    写引用时必须算上前面所有块的头，否则大镜像必然错位。
    """

    def __init__(self):
        self.raw = bytearray()

    def write(self, data):
        """追加记录。

        返回 (块号, 块内内容偏移, 块头的表内磁盘偏移)。
        记录允许跨块（读端会顺延到下一块）。
        """
        p = len(self.raw)
        block = p // METADATA_SIZE
        off = p % METADATA_SIZE
        disk_off = p + 2 * block            # 加上前面每块的 2 字节头
        self.raw.extend(data)
        return block, off, disk_off

    def emit(self):
        """产出磁盘字节：每块 u16(len|0x8000) + 原始内容。"""
        out = bytearray()
        for i in range(0, len(self.raw), METADATA_SIZE):
            chunk = bytes(self.raw[i:i + METADATA_SIZE])
            out += struct.pack('<H', len(chunk) | META_UNCOMPRESSED)
            out += chunk
        return bytes(out)


def mkinode(tbl_off, blk_off):
    """inode 引用编码：(表内字节偏移 << 16) | 块内偏移。"""
    return ((tbl_off << 16) + blk_off) & 0xFFFFFFFFFFFFFFFF


class Builder:
    def __init__(self):
        self.data = bytearray()
        self.inode_tbl = MetaTable()
        self.dir_tbl = MetaTable()

    def store_file(self, node):
        """文件内容写入数据区（逐块 zlib 压缩）。"""
        node.file_size = node.stat.st_size
        if node.file_size == 0:
            return
        node.data_abs = 96 + len(self.data)       # 数据区紧跟 96B superblock
        with open(node.path, 'rb') as f:
            while True:
                chunk = f.read(BLOCK_SIZE)
                if not chunk:
                    break
                comp = zlib.compress(chunk, 6)
                if len(comp) < len(chunk):
                    payload, record = comp, len(comp)
                else:
                    payload, record = chunk, len(chunk) | DATA_UNCOMPRESSED
                self.data.extend(payload)
                node.block_sizes.append(record)

    def inode_reg(self, node):
        """普通文件 inode：16B 头 + start/frag/off/size + 块大小表。"""
        data = struct.pack('<HHHHIIIIII',
                           INODE_REG, disk_mode(node), 0, 0,
                           int(node.stat.st_mtime), node.inode_number,
                           node.data_abs, INVALID_FRAG, 0, node.file_size)
        for rec in node.block_sizes:
            data += struct.pack('<I', rec)
        return self.inode_tbl.write(data)

    def inode_link(self, node):
        # Windows 上 os.readlink 返回反斜杠路径，进镜像必须转成正斜杠，
        # 否则这个软链在 Linux 上无法解析
        target = os.readlink(node.path).encode('utf-8').replace(b'\\', b'/')
        data = struct.pack('<HHHHIIII',
                           INODE_SYMLINK, disk_mode(node), 0, 0,
                           int(node.stat.st_mtime), node.inode_number,
                           1, len(target)) + target
        return self.inode_tbl.write(data)

    def inode_dir(self, node, dir_tbl_off, dir_blk_off, listing_size, nlink, parent_ino):
        data = struct.pack('<HHHHIIIIHHI',
                           INODE_DIR, disk_mode(node), 0, 0,
                           int(node.stat.st_mtime), node.inode_number,
                           dir_tbl_off, nlink,
                           listing_size & 0xFFFF, dir_blk_off & 0xFFFF,
                           parent_ino)
        return self.inode_tbl.write(data)


def build_listing(node):
    """构造目录项字节流：按子 inode 所在 metadata 块分组，组内共享
    DirHeader.start_block（读端用组值 + 各 entry 的块内偏移定位）。
    """
    children = sorted(node.children, key=lambda c: c.name.encode('utf-8'))
    groups = {}
    for c in children:
        groups.setdefault(c.inode_blk_index, []).append(c)

    listing = bytearray()
    for blk in sorted(groups):
        members = groups[blk]
        body = bytearray()
        for c in members:
            if c.kind == 'dir':
                itype, fsize = TYPE_DIR, 3
            elif c.kind == 'link':
                itype = TYPE_SYMLINK
                fsize = len(os.readlink(c.path).encode('utf-8'))
            else:
                itype, fsize = TYPE_REG, c.stat.st_size
            name_b = c.name.encode('utf-8')
            # DirEntry：offset(块内偏移) inode_number(-1) type size(=名字长-1)
            # 磁盘上的名字不带 NUL 结尾（size+1 即完整名字字节数）
            body += struct.pack('<HhHH', c.inode_blk_off, -1, itype, len(name_b) - 1)
            body += name_b
        # DirHeader：count = 组内条目数 - 1
        # start_block = 组所在块头的表内磁盘偏移（块号 × (块大小 + 2字节头)）
        listing += struct.pack('<III', len(members) - 1,
                               blk * (METADATA_SIZE + 2), node.inode_number)
        listing += body
    return bytes(listing)


def build_image(src, out_path, validate=False):
    root, nodes = scan_tree(src)
    b = Builder()
    print('扫描到 %d 个节点' % len(nodes))

    # 1) 数据区
    for node in nodes:
        if node.kind == 'file':
            b.store_file(node)

    # 2) inode：自底向上。文件/软链 inode 在处理其父目录时写入，
    #    保证同目录子项记录连续。
    def handle_dir(node, parent_ino):
        for child in node.children:
            if child.kind == 'dir':
                handle_dir(child, node.inode_number)

        for child in node.children:
            if child.kind == 'file':
                blk_idx, blk_off, _ = b.inode_reg(child)
            elif child.kind == 'link':
                blk_idx, blk_off, _ = b.inode_link(child)
            else:
                continue
            # inode 引用指向所在块的"块头"位置：块号 × (8192 + 2字节头)
            child.inode_blk_index = blk_idx
            child.inode_blk_off = blk_off
            child.inode_hdr_off = blk_idx * (METADATA_SIZE + 2)
            child.inode_ref = mkinode(child.inode_hdr_off, blk_off)

        listing = build_listing(node)
        dir_blk_idx, dir_blk_off, _ = b.dir_tbl.write(listing)
        nlink = 2 + sum(1 for c in node.children if c.kind == 'dir')
        blk_idx, blk_off, _ = b.inode_dir(node, dir_blk_idx * (METADATA_SIZE + 2),
                                          dir_blk_off,
                                          len(listing) + 3, nlink, parent_ino)
        node.inode_blk_index = blk_idx
        node.inode_blk_off = blk_off
        node.inode_hdr_off = blk_idx * (METADATA_SIZE + 2)
        node.inode_ref = mkinode(node.inode_hdr_off, blk_off)

    handle_dir(root, root.inode_number)

    # 3) 组装镜像：superblock(96B) | 数据区 | inode 表 | 目录表 | id 表
    data_area = bytes(b.data)
    inode_area = b.inode_tbl.emit()
    dir_area = b.dir_tbl.emit()

    pos = 96
    pos += len(data_area)
    inode_table_start = pos
    pos += len(inode_area)
    dir_table_start = pos
    pos += len(dir_area)
    id_table_start = pos

    # id 表：索引表（2 项 u64）在前，uid/gid 块（各 2048 个 u32）在后
    def meta_block(payload):
        comp = zlib.compress(payload, 6)
        if len(comp) < len(payload):
            return struct.pack('<H', len(comp)) + comp
        return struct.pack('<H', len(payload) | META_UNCOMPRESSED) + payload

    uid_block = meta_block(struct.pack('<I', 0) * 2048)
    gid_block = meta_block(struct.pack('<I', 0) * 2048)
    id_area = bytearray()
    id_area += struct.pack('<Q', id_table_start + 16)
    id_area += struct.pack('<Q', id_table_start + 16 + len(uid_block))
    id_area += uid_block
    id_area += gid_block
    pos += len(id_area)

    superblock = struct.pack(
        '<IIIIIHHHHHHQQQQQQQQ',
        SQUASHFS_MAGIC,
        len(nodes),                  # inode 数
        int(time.time()),            # mkfs_time
        BLOCK_SIZE,
        0,                           # fragments（不用）
        COMPRESSION_ZLIB,
        BLOCK_LOG,
        0,                           # flags
        4096,                        # no_ids → 索引表 2 项
        4, 0,                        # major / minor
        root.inode_ref,
        pos,                         # bytes_used
        id_table_start,
        INVALID_BLK64,               # xattr（不用）
        inode_table_start,
        dir_table_start,
        INVALID_BLK64,               # fragment 表（不用）
        INVALID_BLK64,               # 导出表（不用）
    )
    assert len(superblock) == 96, len(superblock)

    image = superblock + data_area + inode_area + dir_area + bytes(id_area)
    with open(out_path, 'wb') as f:
        f.write(image)
    print('✓ squashfs 生成：%s（%.1f MB）' % (out_path, len(image) / 1024 / 1024))

    if validate:
        verify_image(out_path, src)
    return out_path


def verify_image(path, src):
    """读回镜像，逐项校验目录树、文件内容与链接目标。"""
    import hashlib
    import PySquashfsImage
    img = PySquashfsImage.SquashFsImage.from_file(path)
    print('--- 读回校验 ---')
    problems = []
    checked = [0]

    def check(disk_dir, rel):
        real_dir = os.path.join(src, rel) if rel else src
        disk_names = {e.name for e in disk_dir.children.values()}
        real_names = set(os.listdir(real_dir))
        if disk_names != real_names:
            problems.append('%s: 条目不一致 缺=%s 多=%s' % (
                rel or '/',
                sorted(real_names - disk_names),
                sorted(disk_names - real_names)))
            return
        for e in disk_dir.children.values():
            r = (rel + '/' + e.name) if rel else e.name
            full = os.path.join(real_dir, e.name)
            if e.is_dir:
                if not os.path.isdir(full) or os.path.islink(full):
                    problems.append('%s: 应为目录' % r)
                    continue
                check(e, r)
            elif os.path.islink(full):
                real_target = os.readlink(full).replace('\\', '/')
                if e.inode.symlink != real_target:
                    problems.append('%s: 链接目标不一致 %s vs %s' %
                                    (r, e.inode.symlink, real_target))
                else:
                    checked[0] += 1
                    print('  ✓ %s → %s' % (r, real_target))
            else:
                try:
                    disk_bytes = b''.join(img.iter_file(e.inode))
                except Exception as ex:
                    problems.append('%s: 读取失败 %s' % (r, ex))
                    continue
                with open(full, 'rb') as f:
                    src_bytes = f.read()
                if hashlib.md5(disk_bytes).hexdigest() != \
                        hashlib.md5(src_bytes).hexdigest():
                    problems.append('%s: 内容不一致（%d vs %d 字节）' %
                                    (r, len(disk_bytes), len(src_bytes)))
                else:
                    checked[0] += 1
                    if len(src_bytes) <= 65536:
                        print('  ✓ %s（%d 字节）' % (r, len(src_bytes)))

    check(img.root, '')
    if problems:
        print('✗ 发现 %d 个问题：' % len(problems))
        for p in problems:
            print('   ', p)
        raise SystemExit(1)
    print('✓ 校验通过：共 %d 个文件/链接内容一致' % checked[0])


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    flags = [a for a in sys.argv[1:] if a.startswith('--')]
    if len(args) < 2:
        print('用法：python squashfs-writer.py <源目录> <输出文件> [--validate]')
        sys.exit(1)
    build_image(os.path.abspath(args[0]), os.path.abspath(args[1]),
                validate='--validate' in flags)


if __name__ == '__main__':
    main()
