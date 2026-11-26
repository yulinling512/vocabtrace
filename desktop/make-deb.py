#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 electron-builder 解好的 linux-unpacked 封装成 .deb。

为什么需要它：electron-builder 的 deb target 依赖 Ruby 的 fpm，
AppImage target 依赖 Linux 的 mksquashfs —— 这两个在 Windows 上都跑不了。
但解包（packaging）那一步是跨平台的，已经成功了，只差最后的封装。

deb 结构（ar 归档）：
  debian-binary      "2.0"
  control.tar.gz     控制信息（包名、版本、依赖、postinst 脚本）
  data.tar.gz        实际文件

用法：python make-deb.py <linux-unpacked 目录> <输出 deb 路径>
"""
import os
import sys
import gzip
import shutil
import tarfile
import tempfile
import subprocess
import io
import json

HERE = os.path.dirname(os.path.abspath(__file__))

PKG_NAME = 'vocab-trace'
APP_NAME = '词迹'
try:                                    # 版本号跟着 package.json 走，别在两处手改
    with io.open(os.path.join(HERE, 'package.json'), encoding='utf-8') as _f:
        VERSION = json.load(_f)['version']
except Exception:
    VERSION = '1.0.0'
ARCH = 'amd64'
MAINTAINER = '柳重名神 <liuqiwei512@163.com>'
HOMEPAGE = 'https://github.com/vocab-trace/vocab-trace'
DESCRIPTION = '认读型背词工具'
INSTALL_DIR = '/opt/vocab-trace'


def write_control(dest):
    """生成 debian/control 等控制文件。"""
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, 'control'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(
            'Package: %s\n'
            'Version: %s\n'
            'Section: Education\n'
            'Priority: optional\n'
            'Architecture: %s\n'
            'Maintainer: %s\n'
            'Homepage: %s\n'
            'Description: %s\n'
            ' 认读型背单词工具：看英文词能懂中文意思，背诵与默写分开标记，\n'
            '  支持错词本复习、多端云同步、AI 配色与天气时令。\n'
            % (PKG_NAME, VERSION, ARCH, MAINTAINER, HOMEPAGE, DESCRIPTION)
        )

    # md5sums：dpkg 会用它校验文件完整性
    # 这里先留空，dpkg -i 不会因为缺它而拒绝安装

    # postinst：装完建好软链和图标缓存
    postinst = (
        '#!/bin/sh\n'
        'set -e\n'
        'ln -sf ' + INSTALL_DIR + '/vocab-trace /usr/bin/' + PKG_NAME + '\n'
        'chmod 4755 ' + INSTALL_DIR + '/chrome-sandbox 2>/dev/null || true\n'
        'if command -v update-desktop-database >/dev/null 2>&1; then\n'
        '  update-desktop-database -q /usr/share/applications || true\n'
        'fi\n'
        'if command -v gtk-update-icon-cache >/dev/null 2>&1; then\n'
        '  gtk-update-icon-cache -q -f -t /usr/share/icons/hicolor || true\n'
        'fi\n'
        'exit 0\n'
    )
    with open(os.path.join(dest, 'postinst'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(postinst)
    os.chmod(os.path.join(dest, 'postinst'), 0o755)


# Windows 的文件不带可执行位，按文件名显式给权限，其余 644
DEB_EXEC_MODES = {
    'vocab-trace': 0o755,
    'chrome_crashpad_handler': 0o755,
    'chrome-sandbox': 0o4755,      # Electron SUID 沙箱
}


def add_tree(tar, root, arc_prefix):
    """把 root 下的所有文件加进 tar，归档路径统一加前缀。"""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        filenames.sort()
        rel = os.path.relpath(dirpath, root)
        arc_dir = arc_prefix if rel == '.' else os.path.join(arc_prefix, rel)
        ti = tar.gettarinfo(dirpath, arcname=arc_dir)
        ti.mode = 0o755 if ti.isdir() else ti.mode
        ti.uid = ti.gid = 0
        ti.uname = ti.gname = 'root'
        tar.addfile(ti)
        for name in filenames:
            full = os.path.join(dirpath, name)
            if os.path.islink(full):
                ti = tar.gettarinfo(full, arcname=os.path.join(arc_dir, name))
                tar.addfile(ti)
                continue
            ti = tar.gettarinfo(full, arcname=os.path.join(arc_dir, name))
            ti.mode = DEB_EXEC_MODES.get(name, 0o644)
            ti.uid = ti.gid = 0
            ti.uname = ti.gname = 'root'
            with open(full, 'rb') as fh:
                tar.addfile(ti, fh)


def build_data_tar(unpacked, out_path):
    """打 data.tar.gz：应用本体 + 桌面文件 + 图标 + 软链。"""
    with tarfile.open(out_path, 'w:gz', compresslevel=6) as tar:
        # 1) 应用本体 → /opt/vocab-trace/
        add_tree(tar, unpacked, INSTALL_DIR)

        # 2) /usr/bin/ 软链
        info = tarfile.TarInfo('usr/bin')
        info.type = tarfile.DIRTYPE
        info.mode = 0o755
        info.uid = info.gid = 0
        info.uname = info.gname = 'root'
        tar.addfile(info)

        link = tarfile.TarInfo('usr/bin/%s' % PKG_NAME)
        link.type = tarfile.SYMTYPE
        link.linkname = '%s/vocab-trace' % INSTALL_DIR
        link.mode = 0o777
        link.uid = link.gid = 0
        link.uname = link.gname = 'root'
        tar.addfile(link)

        # 3) 桌面文件
        desktop = (
            '[Desktop Entry]\n'
            'Type=Application\n'
            'Version=1.0\n'
            'Name=%s\n'
            'Comment=%s\n'
            'Exec=%s %%U\n'
            'Icon=%s\n'
            'Terminal=false\n'
            'Categories=Education;Languages;\n'
            'StartupWMClass=%s\n'
            % (APP_NAME, DESCRIPTION, PKG_NAME, PKG_NAME, PKG_NAME)
        )
        info = tarfile.TarInfo('usr/share/applications')
        info.type = tarfile.DIRTYPE
        info.mode = 0o755
        info.uid = info.gid = 0
        info.uname = info.gname = 'root'
        tar.addfile(info)

        d = tarfile.TarInfo('usr/share/applications/%s.desktop' % PKG_NAME)
        d.size = len(desktop.encode('utf-8'))
        d.mode = 0o644
        d.uid = d.gid = 0
        d.uname = d.gname = 'root'
        tar.addfile(d, io.BytesIO(desktop.encode('utf-8')))

        # 4) 图标：优先用打包目录同级，再退回源码目录
        icon_candidates = [
            os.path.join(os.path.dirname(os.path.abspath(unpacked)), 'icon-512.png'),
            os.path.join(HERE, 'icon-512.png'),
        ]
        icon_src = next((p for p in icon_candidates if os.path.exists(p)), None)
        icon_dir = 'usr/share/icons/hicolor/512x512/apps'
        info = tarfile.TarInfo('usr/share/icons/hicolor')
        info.type = tarfile.DIRTYPE
        info.mode = 0o755
        info.uid = info.gid = 0
        info.uname = info.gname = 'root'
        tar.addfile(info)

        if os.path.exists(icon_src):
            with open(icon_src, 'rb') as fh:
                data = fh.read()
            i = tarfile.TarInfo('%s/%s.png' % (icon_dir, PKG_NAME))
            i.size = len(data)
            i.mode = 0o644
            i.uid = i.gid = 0
            i.uname = i.gname = 'root'
            tar.addfile(i, io.BytesIO(data))
            print('  图标：%s' % icon_src)
        else:
            print('  ⚠ 找不到 icon-512.png，跳过图标')

def build_control_tar(control_dir, out_path):
    with tarfile.open(out_path, 'w:gz', compresslevel=6) as tar:
        for name in ('control', 'postinst', 'md5sums'):
            p = os.path.join(control_dir, name)
            if not os.path.exists(p):
                continue
            ti = tar.gettarinfo(p, arcname='./' + name)
            ti.uid = ti.gid = 0
            ti.uname = ti.gname = 'root'
            ti.mode = 0o755 if name == 'postinst' else 0o644
            with open(p, 'rb') as fh:
                tar.addfile(ti, fh)


def ar_member(name, data):
    """生成一个 ar 归档成员。

    GNU ar 的 60 字节头布局：
      0-15   name        (16)
      16-27  mtime       (12)
      28-33  uid         (6)
      34-39  gid         (6)
      40-47  mode        (8)
      48-57  size        (10)
      58-59  "`\\n"       (2)
    """
    name_b = name.encode('ascii')
    if len(name_b) > 16:
        raise ValueError('成员名过长，需用 GNU 长名表：%s' % name)
    header = (
        name_b.ljust(16) +
        ('0').ljust(12).encode('ascii') +   # mtime
        ('0').ljust(6).encode('ascii') +    # uid
        ('0').ljust(6).encode('ascii') +    # gid
        ('100644').ljust(8).encode('ascii') +  # mode
        str(len(data)).ljust(10).encode('ascii') +  # size
        b'`\n'                            # ar magic
    )
    assert len(header) == 60, len(header)
    out = header + data
    if len(data) % 2 == 1:
        out += b'\n'                     # ar 要求成员长度为偶数
    return out


def write_deb(debian_bin, control_tgz, data_tgz, out_path):
    with open(out_path, 'wb') as f:
        f.write(b'!<arch>\n')
        f.write(ar_member('debian-binary', debian_bin))
        f.write(ar_member('control.tar.gz', control_tgz))
        f.write(ar_member('data.tar.gz', data_tgz))


def main():
    if len(sys.argv) < 3:
        print('用法：python make-deb.py <linux-unpacked 目录> <输出 deb 路径>')
        sys.exit(1)

    unpacked = os.path.abspath(sys.argv[1])
    out_path = os.path.abspath(sys.argv[2])

    if not os.path.isdir(unpacked):
        print('✗ 目录不存在：%s' % unpacked)
        sys.exit(1)

    exe = os.path.join(unpacked, 'vocab-trace')
    if not os.path.exists(exe):
        exe = os.path.join(unpacked, '词迹')
    if not os.path.exists(exe):
        print('✗ 在 %s 里找不到主程序' % unpacked)
        sys.exit(1)

    print('打包 deb：%s' % out_path)
    tmp = tempfile.mkdtemp(prefix='mkdeb_')
    try:
        cdir = os.path.join(tmp, 'debian')
        write_control(cdir)

        control_tgz = os.path.join(tmp, 'control.tar.gz')
        build_control_tar(cdir, control_tgz)
        print('  control.tar.gz 完成')

        data_tgz = os.path.join(tmp, 'data.tar.gz')
        build_data_tar(unpacked, data_tgz)
        print('  data.tar.gz 完成')

        with open(control_tgz, 'rb') as f:
            c_data = f.read()
        with open(data_tgz, 'rb') as f:
            d_data = f.read()

        write_deb(b'2.0\n', c_data, d_data, out_path)
        size = os.path.getsize(out_path)
        print('✓ 完成：%s（%.1f MB）' % (out_path, size / 1024 / 1024))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
