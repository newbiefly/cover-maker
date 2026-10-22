# -*- coding: utf-8 -*-
"""渲染层：模板 + 标题 → HTML → PNG。画布尺寸由模板决定。"""
import os
import shutil
import subprocess
from pathlib import Path

import core

HERE = Path(__file__).resolve().parent

_BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]

FONT_STACK = ('"Microsoft YaHei","PingFang SC","Noto Sans SC",'
              '"Source Han Sans SC","Hiragino Sans GB",sans-serif')


def find_browser(explicit=None):
    if explicit:
        p = Path(os.path.expanduser(explicit))
        if p.exists():
            return str(p)
        raise RuntimeError("指定的浏览器不存在: %s" % explicit)
    for c in _BROWSERS:
        if Path(c).exists():
            return c
    for name in ("msedge", "chrome", "chromium", "google-chrome"):
        w = shutil.which(name)
        if w:
            return w
    raise RuntimeError("找不到 Edge 或 Chrome。Windows 一般自带 Edge；"
                       "也可用 --browser 指定可执行文件路径。")


def build_html(tpl, ctx):
    """模板 + 字段 → 完整 HTML。"""
    body, css = tpl.render(ctx)
    return ('<!DOCTYPE html><html><head><meta charset="utf-8"><style>'
            '*{margin:0;padding:0;box-sizing:border-box}'
            'html,body{width:%dpx;height:%dpx;overflow:hidden}'
            'body{font-family:%s;-webkit-font-smoothing:antialiased}'
            '#root{width:%dpx;height:%dpx;position:relative;overflow:hidden}'
            % (tpl.w, tpl.h, FONT_STACK, tpl.w, tpl.h)
            + css + '</style></head><body><div id="root">'
            + body + '</div></body></html>')


def shoot(html, out_png, w, h, browser=None):
    """无头截图。浏览器对中文路径不可靠，先截到 ASCII 临时路径再改名。"""
    exe = find_browser(browser)
    tmp = HERE / "_tmp"
    tmp.mkdir(exist_ok=True)
    tmp_html, tmp_png = tmp / "page.html", tmp / "shot.png"
    tmp_html.write_text(html, encoding="utf-8")
    if tmp_png.exists():
        tmp_png.unlink()
    subprocess.run([exe, "--headless", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=1",
                    "--window-size=%d,%d" % (w, h),
                    "--screenshot=" + str(tmp_png),
                    "file:///" + str(tmp_html).replace("\\", "/")],
                   capture_output=True)
    if not tmp_png.exists():
        return False
    out_png = Path(out_png)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    if out_png.exists():
        out_png.unlink()
    shutil.move(str(tmp_png), str(out_png))   # 可能跨盘，不能用 Path.replace
    return True


def make(tpl, title, out_png, browser=None, **kw):
    """一步出图。返回是否成功。"""
    ctx = core.parse(title, canvas_w=tpl.w, **kw)
    return shoot(build_html(tpl, ctx), out_png, tpl.w, tpl.h, browser)
