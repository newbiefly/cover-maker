# -*- coding: utf-8 -*-
"""通用工具层：画布预设、标题解析、文章取标题、排版辅助。

这里不含任何具体封面风格——风格由 templates/ 下的模板决定。
"""
import re
from pathlib import Path

# ---------------- 画布预设 ----------------
# 名称 → (宽, 高, 说明)
PRESETS = {
    "3:4":    (1080, 1440, "小红书首图 / 笔记配图（默认）"),
    "9:16":   (1080, 1920, "小红书视频封面 / 抖音 / 竖版短视频"),
    "1:1":    (1080, 1080, "方图 / 头像位 / 朋友圈"),
    "16:9":   (1920, 1080, "B站 / 横版视频 / 幻灯片"),
    "2.35:1": (900,  383,  "公众号头图"),
}
DEFAULT_SIZE = "3:4"


def parse_size(spec):
    """'3:4' / '1080x1440' / '1080*1440' → (宽, 高)。"""
    s = str(spec or DEFAULT_SIZE).strip().lower()
    if s in PRESETS:
        return PRESETS[s][0], PRESETS[s][1]
    m = re.match(r"^(\d+)\s*[x*×]\s*(\d+)$", s)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.match(r"^(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)$", s)
    if m:                                   # 任意比例 → 以 1080 为基准边
        a, b = float(m.group(1)), float(m.group(2))
        return (1080, int(round(1080 * b / a))) if a >= b else (int(round(1080 * a / b)), 1080)
    raise ValueError("看不懂的尺寸: %s（可用 %s 或 1080x1440）"
                     % (spec, " / ".join(PRESETS)))


def size_label(w, h):
    for k, (pw, ph, _) in PRESETS.items():
        if (pw, ph) == (w, h):
            return k
    return "%dx%d" % (w, h)


# ---------------- HTML 辅助 ----------------
def esc(s):
    return (str(s) if s is not None else "").replace(
        "&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# 数字 + 量词：7大 / 5种 / 3秒 / 100倍 / 911篇 / 35.6%
_NUM_RE = re.compile(r"(\d+(?:\.\d+)?\s*(?:大|种|条|个|招|层|式|倍|秒|篇|章|年|月|天|次|步|分|%|％)?)")


def hero_html(title, cls="o"):
    """完整标题 → HTML，数字（含量词）自动包上高亮 span。

    模板里给 .o 一个强调色就能免费拿到"数字跳出来"的效果。
    """
    return _NUM_RE.sub(lambda m: '<span class="%s">%s</span>' % (cls, m.group(1)),
                       esc(title or ""))


def hero_px(title, canvas_w=1080, pad=80, lines=3):
    """标题字号自适应。

    按"画布可用宽度 / 每行容纳字数"反推，所以换比例也成立：
    9:16 和 3:4 同宽，字号一致；16:9 更宽，同样字数可以更大。
    """
    n = len(title or "")
    if n <= 0:
        return 96
    usable = max(canvas_w - pad * 2, 200)
    per_line = max(1, (n + lines - 1) // lines)     # 均摊到 lines 行
    px = int(usable / max(per_line, 1) * 0.98)
    return max(48, min(px, 150))


# ---------------- 标题 → 字段 ----------------
_NUM_UNIT = re.compile(r"(\d+(?:\.\d+)?)\s*(大|种|条|个|招|层|式|倍|秒|篇|章|年|月|天|次|步|%|％)?")
_STOP = "的了是在和与就都也而又并把被让使这那"


def parse(title, key=None, wrong=None, num=None, seq="01", total="10",
          query=None, canvas_w=1080, **extra):
    """从标题推断模板所需字段。能自动的尽量自动，拿不准的给安全兜底。

    extra 里的键会原样并入 ctx，方便模板用自定义占位符。
    """
    t = (title or "").strip()

    if not num:
        m = _NUM_UNIT.search(t)
        num = m.group(1) if m else ""

    if not key:
        m = _NUM_UNIT.search(t)
        rest = t[m.end():] if m else t
        rest = re.split(r"[：:，,。！!？?\s]", rest.lstrip(_STOP))[0]
        key = rest[:8] or t[:8]

    m = re.search(r"[：:]", t)
    head, tail = (t[:m.start()], t[m.end():]) if m else (t, "")

    ctx = {
        "title": t,
        "title_html": hero_html(t),
        "head": head, "tail": tail,
        "key": key or "",
        "wrong": wrong or "",
        "num": str(num or ""),
        "seq": str(seq), "total": str(total),
        "query": query or "",
        "hero_px": hero_px(t, canvas_w),
    }
    ctx.update({k: v for k, v in extra.items() if v is not None})
    return ctx


# ---------------- 文章 → 标题 ----------------
ARTICLE_EXT = (".md", ".markdown", ".txt")


def title_of_article(path):
    """从一篇文章取标题：正文首个 # 标题 → 文件名（去编号前缀）→ 首行非空正文。"""
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        text = p.read_text(encoding="gbk", errors="ignore")
    except Exception:
        text = ""

    lines = [l.strip() for l in text.splitlines()]
    for l in lines[:40]:
        m = re.match(r"^#{1,3}\s+(.+?)\s*#*$", l)
        if m and m.group(1).strip():
            return m.group(1).strip()

    stem = re.sub(r"^\d+[-_.\s]*", "", p.stem).strip()
    if stem:
        return stem
    for l in lines:
        if l and not l.startswith(("---", "```", ">")):
            return l.lstrip("#").strip()
    return p.stem


def collect_articles(path):
    """单篇或整目录 → [(标题, 路径), ...]。目录按文件名里的数字排序。"""
    p = Path(path)
    if not p.exists():
        raise RuntimeError("找不到文章或目录: %s" % path)
    files = [p] if p.is_file() else [
        f for f in p.iterdir()
        if f.is_file() and f.suffix.lower() in ARTICLE_EXT and not f.name.startswith("_")
    ]

    def _k(f):
        m = re.match(r"^(\d+)", f.stem)
        return (0, int(m.group(1)), f.stem) if m else (1, 0, f.stem)

    files.sort(key=_k)
    return [(title_of_article(f), f) for f in files]


def safe_name(s, limit=80):
    s = re.sub(r"[:：]", " ", s or "")
    s = re.sub(r'[\\/*?"<>|]', "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:limit] or "cover"
