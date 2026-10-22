# 模板文件规范

一个模板 = 一个 `.html` 文件。三部分：元数据块、`<style>`、HTML。

## 最小可用文件

```html
<!-- cover-template
     name: 风格名
     size: 3:4
     note: 适合什么内容
-->
<style>
  #root { background: #FFFFFF; }
  /* 你的版式 CSS */
</style>

<!-- 你的版式 HTML，至少要让标题出现 -->
```

这样就能用了：

```powershell
py -3 cover.py -t "标题" -s 风格名
```

**这里刻意不给具体版式。** 文档里的示例版式会变成设计锚点——照着改，所有模板都会长成同一个样。版式从结构想起，方法见 `design-guide.md`。

## 元数据块

```html
<!-- cover-template
     name: 显示名（挑模板时用这个名字）
     size: 3:4 | 9:16 | 1:1 | 16:9 | 2.35:1 | 1242x1660
     note: 一句话说清适合什么内容
-->
```

- 三个字段都可省。`name` 默认取文件名，`size` 默认 `3:4`，`note` 默认空
- 中文键也认：`名称` / `比例` / `用途` / `说明`
- `size` 写任意比例（如 `4:5`）会以 1080 为基准长边换算
- 文件名以 `_` 开头 = 草稿，不进模板列表（改到一半不想被用上时很方便）

## 占位符

纯文本替换，不执行逻辑。写错名字不报错，会原样留在画面上。

下表的「例」一列以标题「新手最容易踩的5个坑：第3个最致命」为例。

| 占位符 | 内容 | 例 |
|---|---|---|
`{{title}}` | 纯文本标题 | `新手最容易踩的5个坑：第3个最致命` |
`{{title_html}}` | 标题，数字含量词已包 `<span class="o">` | `新手最容易踩的<span class="o">5个</span>坑：第<span class="o">3个</span>最致命` |
`{{head}}` | 冒号前的主句 | `新手最容易踩的5个坑` |
`{{tail}}` | 冒号后的副句 | `第3个最致命`（无冒号时为空串） |
`{{key}}` | 核心词（数字量词之后的词组，≤8字） | `坑` |
`{{wrong}}` | 对立面/错误认知 | 空，需 `--wrong` 指定 |
`{{num}}` | 标题里第一个数字 | `5` |
`{{seq}}` / `{{total}}` | 连载序号 | `01` / `10` |
`{{query}}` | 提问类风格的问句 | 空，需 `--query` 指定 |
`{{hero_px}}` | 建议字号（纯数字，不带 px） | `98` |

### 几个要点

**`{{title_html}}` 免费给你数字高亮**，只需给 `.o` 一个样式（颜色、字重、底色块都行）。标题里有不想强调的数字（年份、价格）时改用 `{{title}}` 自己手工包。

**`{{hero_px}}` 是建议值，不是必须用。** 它按字数均摊约 3 行反推，只在标题是大块主文本时合适。标题嵌在气泡、便签、列表项、票根里的时候**别用它**——会把版式拉回"大块居中文本"。那些情况按容器自己定字号。

要用的话记得自己拼单位：`font-size: {{hero_px}}px`，占位符本身只是数字。

**可能为空的占位符要考虑空态**。`{{wrong}}` `{{query}}` 默认是空串，用户没传就什么都不显示。如果你的设计强依赖它（比如"划掉对立面"的版式），在 `note` 里写明需要 `--wrong`，否则会出现一个空白色块。

**自定义占位符**：`core.parse()` 的 `**extra` 会原样并入，所以脚本调用时传什么键，模板里就能用 `{{那个键}}`。命令行目前没开放任意键，需要时改 `cover.py` 的 `_kw()`。

## CSS 约定

渲染时外层已经注入了这些，模板里不用重复写：

```css
* { margin:0; padding:0; box-sizing:border-box }
html, body { width:<W>px; height:<H>px; overflow:hidden }
body { font-family: 微软雅黑/苹方/思源黑体链; -webkit-font-smoothing:antialiased }
#root { width:<W>px; height:<H>px; position:relative; overflow:hidden }
```

所以：

- **`#root` 是根容器**，已有尺寸和 `position:relative`，子元素直接 `position:absolute` 定位
- **字体别自己声明**，除非你确实要换（比如用衬线体做故事感，`font-family: "Songti SC", serif`）
- **尺寸写死 px 没问题**，画布尺寸固定，不需要响应式
- `<style>` 块可以有多个，会被合并；HTML 注释会被剥掉

### 能用什么

跑在 Chromium 无头浏览器里，现代 CSS 基本都能用：渐变、`clip-path`、`transform`、`filter`、`mix-blend-mode`、伪元素、`box-shadow`、SVG 内联。

不能用：

- **外部资源** —— 网络字体、远程图片都不行（无头截图不等网络）。要用图片就内联 base64
- **JS** —— 不执行脚本
- **动画** —— 截的是静止帧，`animation` 无意义

## 调试

```powershell
# 出样张（用真实标题，别用"示例标题"）
py -3 cover.py -t "用户的真实标题" -s 模板名 -o _preview

# 打开看
Start-Process _preview\xxx.png

# 多套对比
py -3 cover.py -t "真实标题" --all -o _preview

# 自检：渲染一遍 + 查未替换的占位符
py -3 doctor.py
```

### 想看生成的 HTML

渲染时的中间文件在 `scripts/_tmp/page.html`，出图后还留着。直接用浏览器打开它就能开 DevTools 调样式，调好再抄回模板。这是改版式最快的路子。

## 模板放哪

查找顺序：

1. `--templates 目录` 显式指定
2. 环境变量 `COVER_TEMPLATES`
3. **当前工作目录下的 `cover-templates/`** ← 默认
4. skill 自带的 `templates/`（只有格式说明文件）

默认放工作区是有意的：不同账号、不同项目的风格不该混在一起，而且 skill 升级不会覆盖你的模板。

同名模板以工作区的为准。

## 常见错误

**封面上出现 `{{titel}}` 这种字样**
占位符拼错。`doctor.py` 会报出是哪套模板。

**模板不出现在 `--list` 里**
文件名以 `_` 开头，或不在模板目录下，或后缀不是 `.html`。

**元素全部堆在左上角**
忘了 `position: absolute`。`#root` 是 relative 容器，子元素不定位就按文档流排。

**内容被裁掉**
`#root` 是 `overflow:hidden`。超出画布的部分不会出现在截图里——这通常是好事（可以故意让大数字出血），但要确认裁的是装饰不是标题。

**长标题溢出画布**
`{{hero_px}}` 只控字号不控容器高度。给标题容器留足空间，或者用最长的真实标题测一遍。
