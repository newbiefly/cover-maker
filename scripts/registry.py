# -*- coding: utf-8 -*-
"""模板库：扫描、解析元数据、渲染。

模板就是一个 .html 文件，放在模板目录下。模板目录的查找顺序：
  1. 显式传入（CLI 的 --templates）
  2. 环境变量 COVER_TEMPLATES
  3. 当前工作目录下的 cover-templates/     ← 默认，模板跟着项目走
  4. skill 自带的 templates/（只有格式说明文件，不是成品风格）
"""
import os
import re
from pathlib import Path

import core

HERE = Path(__file__).resolve().parent
SKILL_TPL = HERE.parent / "templates"
WORK_TPL_NAME = "cover-templates"


def template_dir(explicit=None, create=False):
    if explicit:
        d = Path(explicit).expanduser()
    elif os.environ.get("COVER_TEMPLATES"):
        d = Path(os.environ["COVER_TEMPLATES"]).expanduser()
    else:
        d = Path.cwd() / WORK_TPL_NAME
    if create:
        d.mkdir(parents=True, exist_ok=True)
    return d


def search_dirs(explicit=None):
    """实际会被扫描的目录列表（工作区优先，skill 示例垫底）。"""
    out = [template_dir(explicit)]
    if SKILL_TPL.exists() and SKILL_TPL.resolve() != out[0].resolve():
        out.append(SKILL_TPL)
    return out


# ---------------- 元数据 ----------------
_META_RE = re.compile(r"<!--\s*cover-template\s*(.*?)-->", re.S)


def parse_meta(path, text):
    """读模板头部的元数据块。

        <!-- cover-template
             name: 风格名
             size: 3:4
             note: 适合什么内容
        -->

    也兼容单行写法 <!-- cover-template: 名字 -->。
    """
    meta = {"name": path.stem, "size": core.DEFAULT_SIZE, "note": ""}
    m = _META_RE.search(text)
    if not m:
        return meta
    block = m.group(1).strip()
    if block.startswith(":") and "\n" not in block:          # 老式单行
        meta["name"] = block.lstrip(":").strip() or path.stem
        return meta
    for line in block.splitlines():
        line = line.strip().lstrip("*").strip()
        kv = re.match(r"^(name|size|note|用途|说明|比例|名称)\s*[:：]\s*(.+)$", line, re.I)
        if kv:
            k, v = kv.group(1).lower(), kv.group(2).strip()
            k = {"名称": "name", "比例": "size", "用途": "note", "说明": "note"}.get(k, k)
            meta[k] = v
    return meta


class Template(object):
    def __init__(self, path, text, meta):
        self.path, self.text = path, text
        self.name = meta["name"]
        self.size = meta["size"]
        self.note = meta["note"]
        try:
            self.w, self.h = core.parse_size(self.size)
        except ValueError:
            self.w, self.h = core.parse_size(core.DEFAULT_SIZE)

    def __repr__(self):
        return "<Template %s %dx%d>" % (self.name, self.w, self.h)

    def render(self, ctx):
        """→ (body_html, css)。占位符纯文本替换，不执行逻辑。"""
        s = self.text
        s = _META_RE.sub("", s, count=1)
        for k, v in ctx.items():
            s = s.replace("{{%s}}" % k, str(v))
        css = "\n".join(re.findall(r"<style>(.*?)</style>", s, re.S))
        body = re.sub(r"<style>.*?</style>", "", s, flags=re.S)
        body = re.sub(r"<!--.*?-->", "", body, flags=re.S).strip()
        return body, css


def scan(explicit=None):
    """扫描模板，返回 [Template, ...]。同名时工作区的覆盖 skill 自带的。"""
    found, seen = [], set()
    for d in search_dirs(explicit):
        if not d.exists():
            continue
        for p in sorted(d.glob("*.html")):
            if p.name.startswith("_"):          # 下划线开头 = 草稿/示例，不进列表
                continue
            try:
                text = p.read_text(encoding="utf-8-sig")
            except Exception:
                continue
            meta = parse_meta(p, text)
            if meta["name"] in seen:
                continue
            seen.add(meta["name"])
            found.append(Template(p, text, meta))
    return found


def pick(templates, spec=None, index=0):
    """按名称或编号取模板；都没给就按 index 轮转。"""
    if not templates:
        return None
    if spec:
        key = str(spec).strip()
        if key.isdigit() and 1 <= int(key) <= len(templates):
            return templates[int(key) - 1]
        for t in templates:
            if key == t.name:
                return t
        for t in templates:
            if key.lower() == t.name.lower() or key.lower() == t.path.stem.lower():
                return t
        hits = [t for t in templates if key in t.name]
        if len(hits) == 1:
            return hits[0]
        if len(hits) > 1:
            raise RuntimeError("「%s」匹配到多个模板：%s，请写全名"
                               % (key, "、".join(t.name for t in hits)))
        raise RuntimeError("找不到模板「%s」。现有：%s"
                           % (key, "、".join(t.name for t in templates) or "（空）"))
    return templates[index % len(templates)]


# ---------------- 新建骨架 ----------------
# 刻意不预设版式：骨架里给一个 .hero 大标题会把后续设计全部拽向"居中大字"。
# 这里只给文件契约（元数据 + 空容器 + 材料清单），版式从零写。
SKELETON = """<!-- cover-template
     name: %(name)s
     size: %(size)s
     note: 一句话写清适合什么内容，方便以后挑
-->
<!--
  ⚠ 这是空白文件，不是起手版式。别指望在这儿"改改就能用"——
    先定好结构（标题长在什么东西上？），再从零写 CSS 和 HTML。

  画布 %(w)dx%(h)d。#root 是根容器，已设好尺寸和 position:relative，
  子元素直接 position:absolute 定位。字体已在外层设好，不用声明。

  可用的材料（纯文本替换，不执行逻辑，用不到的不用管）：
    {{title}}       纯文本标题
    {{title_html}}  标题，数字已自动包上 class="o" 的 span
    {{head}}/{{tail}}  标题按冒号切分的主句/副句
    {{key}} 核心词   {{wrong}} 对立面   {{num}} 数字
    {{seq}}/{{total}} 连载序号   {{query}} 问句
    {{hero_px}}     一个按字数算的建议字号。标题是大块主文本时好用，
                    标题嵌在气泡/便签/列表项里时别用它，自己定字号。

  规范: references/template-spec.md    设计方法: references/design-guide.md
-->
<style>
  #root { background: #FFFFFF; }
</style>
"""


def new_template(name, size=None, out_dir=None):
    d = template_dir(out_dir, create=True)
    w, h = core.parse_size(size or core.DEFAULT_SIZE)
    out = d / ("%s.html" % core.safe_name(name, 40))
    out.write_text(SKELETON % {
        "name": name, "size": size or core.DEFAULT_SIZE, "w": w, "h": h,
    }, encoding="utf-8")
    return out
