# -*- coding: utf-8 -*-
r"""封面出图命令行。

这里只负责"用已有模板出图"。风格设计走 SKILL.md 的六步流程。

  # 看现有模板
  py -3 cover.py --list

  # 新建一个空白模板（再把设计写进去）
  py -3 cover.py --new 风格名 --size 3:4

  # 用某个模板出一张
  py -3 cover.py -t "标题" -s 风格名

  # 挑风格：同一个标题，每套模板各出一张
  py -3 cover.py -t "标题" --all

  # 从文章出图（单篇或整目录，自动取标题）
  py -3 cover.py -a 文章.md -s 风格名
  py -3 cover.py -a 文章目录 -s 风格名

  # 从标题清单批量
  py -3 cover.py -f titles.txt -s 风格名
"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import core
import registry as REG
import render as R


def _kw(a):
    return dict(key=a.key, wrong=a.wrong, num=a.num,
                seq=a.seq, total=a.total, query=a.query)


def no_template_hint(a):
    d = REG.template_dir(a.templates)
    print("模板库是空的 —— %s" % d)
    print()
    print("封面风格需要先设计出来，两条路：")
    print("  1 让 agent 设计（推荐）：把你的标题或文章给它，说\"帮我设计封面风格\"，")
    print("    它会问清用途/比例/调性，给几个方向，然后写模板、出样张、按你的反馈改。")
    print("  2 自己动手：py -3 cover.py --new 风格名 --size 3:4，然后编辑生成的 html。")
    print()
    print("模板格式见 references/template-spec.md，设计要点见 references/design-guide.md")


def one(tpl, title, out_dir, a, tag=""):
    png = Path(out_dir) / ("%s%s.png" % (core.safe_name(title), tag))
    ok = R.make(tpl, title, png, browser=a.browser, **_kw(a))
    print("%s %-12s %dx%d  %s" % ("[ OK ]" if ok else "[FAIL]",
                                  tpl.name, tpl.w, tpl.h, png.name))
    return png if ok else None


def main():
    ap = argparse.ArgumentParser(
        description="封面出图：标题或文章 + 模板 → PNG",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("-t", "--title", help="单个标题")
    ap.add_argument("-a", "--article", help="文章文件或目录（自动取标题）")
    ap.add_argument("-f", "--file", help="标题清单文件，一行一个")
    ap.add_argument("-s", "--style", help="模板名或编号（不填用第一个）")
    ap.add_argument("-o", "--out", default="covers", help="输出目录，默认 covers")
    ap.add_argument("--all", action="store_true",
                    help="单标题时每个模板各出一张（挑风格用）；批量时多套风格轮转")
    ap.add_argument("--templates", help="模板目录（默认 ./cover-templates）")
    ap.add_argument("--list", action="store_true", help="列出现有模板")
    ap.add_argument("--new", metavar="名称", help="新建模板骨架")
    ap.add_argument("--size", help="新建模板时的画布：3:4 / 9:16 / 1:1 / 16:9 / 1080x1440")
    ap.add_argument("--sizes", action="store_true", help="列出画布预设")
    ap.add_argument("--key", help="核心词（默认从标题推断）")
    ap.add_argument("--wrong", help="对立面/错误认知（部分风格用）")
    ap.add_argument("--num", help="数字（默认取标题里第一个）")
    ap.add_argument("--seq", default="01", help="连载序号")
    ap.add_argument("--total", default="10", help="连载总数")
    ap.add_argument("--query", help="提问类风格的问句")
    ap.add_argument("--browser", help="浏览器可执行文件路径（默认自动探测）")
    a = ap.parse_args()

    if a.sizes:
        print("画布预设:")
        for k, (w, h, note) in core.PRESETS.items():
            print("  %-7s %4dx%-5d %s" % (k, w, h, note))
        print("\n也可直接写像素: --size 1242x1660")
        return

    if a.new:
        p = REG.new_template(a.new, a.size, a.templates)
        print("已新建空白模板: %s" % p)
        print("这是空文件，不含任何版式 —— 先想清结构（标题长在什么东西上），再从零写")
        print("出样张: py -3 cover.py -t \"你的标题\" -s \"%s\"" % a.new)
        return

    tpls = REG.scan(a.templates)

    if a.list:
        if not tpls:
            no_template_hint(a)
            return
        print("模板库（%s）:" % REG.template_dir(a.templates))
        for i, t in enumerate(tpls, 1):
            print("  %2d  %-14s %-9s %s" % (i, t.name, core.size_label(t.w, t.h), t.note))
        return

    if not (a.title or a.article or a.file):
        ap.error("请给一个输入：-t 标题 / -a 文章或目录 / -f 标题清单（或用 --list / --new）")

    if not tpls:
        no_template_hint(a)
        sys.exit(1)

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    # 收集要出图的标题
    if a.title:
        pairs = [(a.title, None)]
    elif a.article:
        pairs = core.collect_articles(a.article)
        if not pairs:
            print("目录里没有 .md / .txt 文章")
            return
        print("读到 %d 篇文章" % len(pairs))
    else:
        lines = [l.strip() for l in
                 Path(a.file).read_text(encoding="utf-8-sig").splitlines()]
        pairs = [(l, None) for l in lines if l and not l.startswith("#")]
        if not pairs:
            print("清单为空（空行与 # 开头的行会被忽略）")
            return
        print("读到 %d 个标题" % len(pairs))

    print("输出: %s\n" % out.resolve())

    # 模式一：一个标题 × 全部模板（设计阶段挑风格用，每套各出一张）
    if a.all and len(pairs) == 1:
        title = pairs[0][0]
        print("标题: %s\n" % title)
        made = [p for p in (one(t, title, out, a, tag="__%02d-%s" % (i, t.name))
                            for i, t in enumerate(tpls, 1)) if p]
        print("\n成功 %d / %d" % (len(made), len(tpls)))
        return

    # 模式二：指定模板（或多套轮转）批量出图
    rotate = a.all and len(pairs) > 1
    made = []
    for i, (title, src) in enumerate(pairs):
        tpl = REG.pick(tpls, None, i) if rotate else REG.pick(tpls, a.style, 0)
        p = one(tpl, title, out, a)
        if p:
            made.append(p)

    if len(made) != len(pairs) or len(pairs) > 1:
        print("\n成功 %d / %d" % (len(made), len(pairs)))


if __name__ == "__main__":
    main()
