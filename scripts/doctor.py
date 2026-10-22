# -*- coding: utf-8 -*-
"""环境与模板自检。用法: py -3 doctor.py [--templates 目录]"""
import platform
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

OK, WARN, FAIL = "[ OK ]", "[WARN]", "[FAIL]"
fails = warns = 0

explicit = None
if "--templates" in sys.argv:
    i = sys.argv.index("--templates")
    explicit = sys.argv[i + 1] if len(sys.argv) > i + 1 else None


def log(level, item, detail="", fix=""):
    global fails, warns
    if level == FAIL:
        fails += 1
    if level == WARN:
        warns += 1
    print("%s %s%s" % (level, item, ("  —  " + detail) if detail else ""))
    if fix and level != OK:
        print("       修复: %s" % fix)


print("=" * 60)
print(" 封面设计器 · 自检")
print("=" * 60)

v = sys.version_info
if v >= (3, 7):
    log(OK, "Python %d.%d.%d" % (v.major, v.minor, v.micro))
else:
    log(FAIL, "Python 版本过低", "%d.%d" % (v.major, v.minor), "装 Python 3.7+")

try:
    import core
    import registry as REG
    import render as R
    log(OK, "模块加载")
except Exception as e:
    log(FAIL, "模块导入失败", str(e)[:70])
    sys.exit(1)

try:
    log(OK, "浏览器", R.find_browser())
except Exception as e:
    log(FAIL, "找不到浏览器", str(e).splitlines()[0],
        "Windows 一般自带 Edge；或用 --browser 指定路径")

if platform.system() == "Windows":
    hit = [c for c in ("msyh.ttc", "msyhbd.ttc", "simhei.ttf")
           if (Path("C:/Windows/Fonts") / c).exists()]
    log(OK if hit else WARN,
        "中文字体", "微软雅黑/黑体可用" if hit else "未检测到常见中文字体",
        "" if hit else "安装微软雅黑或思源黑体")
else:
    log(WARN, "非 Windows", "请确认已装 PingFang / 思源黑体等中文字体")

# ---------------- 模板自检 ----------------
tdir = REG.template_dir(explicit)
tpls = REG.scan(explicit)
if not tpls:
    log(WARN, "模板库为空", str(tdir),
        "让 agent 按你的内容设计一套，或 py -3 cover.py --new 风格名")
else:
    log(OK, "模板库", "%d 套  @ %s" % (len(tpls), tdir))
    demo = core.parse("示例标题7种方法让你一看就懂：副标题在这里")
    bad = []
    for t in tpls:
        try:
            ctx = core.parse(demo["title"], canvas_w=t.w)
            html = R.build_html(t, ctx)
            assert "#root" in html, "缺少根容器"
            assert len(html) > 200, "内容过短"
            left = [x for x in ("{{", "}}") if x in html]
            assert not left, "有未替换的占位符（名字可能拼错了）"
        except Exception as e:
            bad.append("%s(%s)" % (t.name, str(e)[:40]))
    if bad:
        log(FAIL, "模板自检未通过", "；".join(bad),
            "对照 references/template-spec.md 检查占位符拼写")
    else:
        log(OK, "模板自检", "%d 套全部可正常渲染" % len(tpls))
        for t in tpls:
            print("       · %-14s %-9s %s" % (t.name, core.size_label(t.w, t.h), t.note))

print("=" * 60)
if fails:
    print(" 不可用：%d 项致命问题。" % fails)
    sys.exit(1)
print(" 就绪%s。" % ("（%d 项提示）" % warns if warns else ""))
print("=" * 60)
