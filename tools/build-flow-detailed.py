import io, os

REF = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references"))
OUT = os.path.join(REF, "flow-detailed.svg")

C = {"text": "#1f2328", "dim": "#656d76", "line": "#d0d7de",
     "l1": "#0969da", "l2": "#bf8700", "l3": "#cf222e", "ok": "#1a7f37",
     "purple": "#8250df",
     "l1bg": "#ddf4ff", "l2bg": "#fff8c5", "l3bg": "#ffebe9", "okbg": "#dafbe1",
     "gray": "#f6f8fa"}

p = []
A = p.append

def rect(x, y, w, h, fill, stroke, rx=8, sw=1):
    A(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

def txt(x, y, s, size=11, fill=None, weight=None, anchor=None):
    f = fill or C["text"]; w = f' font-weight="{weight}"' if weight else ""
    a = f' text-anchor="{anchor}"' if anchor else ""
    A(f'<text x="{x}" y="{y}" font-size="{size}"{w}{a} fill="{f}">{s}</text>')

def box(x, y, w, h, title, lines, fill, stroke, tfs=11.5, lfs=9.8):
    rect(x, y, w, h, fill, stroke)
    txt(x + 11, y + 18, title, tfs, C["text"], "600")
    for i, t in enumerate(lines):
        txt(x + 11, y + 33 + i * 13, t, lfs, C["dim"])

def arrow(x1, y1, x2, y2, color, label=None, lx=None, ly=None, ls=9.2):
    A(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="1.5" marker-end="url(#ar)"/>')
    if label:
        txt(lx if lx else (x1+x2)//2, ly if ly else (y1+y2)//2 - 4, label, ls, C["dim"], None, "middle")

def tag(x, y, w, label, color, sub, subw=0):
    rect(x, y, w, 21, color, color, 6)
    txt(x + w/2, y + 15, label, 10.5, "#fff", "700", "middle")
    if sub:
        txt(x + w + 11, y + 15, sub, 9.5, color)

W, H = 680, 1330
A(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img">')
A('<title>达芬奇21中文操作手册 · 完整调用流程（首次判定 + 双触发源三态递进 + 回归测试）</title>')
A('<desc>完整流程：阶段零首次使用判定（读状态文件，跨会话只做一次）；阶段一三词典问句归一化；阶段二 L1 极速两轮本地检索；阶段三升级判定双触发源（本地答不上来 / 用户明确要深入）；阶段四 L2 深读联网双重比对；阶段五 L3 兜底明说未覆盖；阶段六答后必问与回写词典；附检索路由表与命中率现状。</desc>')
A('<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#656d76"/></marker></defs>')
rect(0, 0, W, H, "#ffffff", "#ffffff", 0, 0)

txt(340, 24, "完整调用流程 · 首次判定 + 三态递进", 15, C["text"], "700", "middle")
txt(340, 41, "v2.10 · 六阶段 · 命中率 术语 100% / 白话 100%", 10, C["dim"], None, "middle")

# ===== 阶段 0 =====
rect(20, 54, 640, 96, C["gray"], "#c9d1d9", 10, 1.5)
txt(32, 70, "阶段 0 · 首次使用判定（同一用户跨会话只做一次）", 11, C["text"], "700")
box(36, 78, 296, 40, "读状态文件", ["node scripts/check-first-run.js（只读探测）"],
    "#ffffff", "#c9d1d9", 11, 9.5)
box(348, 78, 296, 40, "isFirstRun = false", ["→ 跳过引导，直接问答（不弹图不读SVG）"],
    C["okbg"], C["ok"], 11, 9.5)
arrow(336, 98, 346, 98, C["ok"])
txt(184, 130, "true → 首次：Read flow-overview.svg → show_widget → --mark 落盘", 9.2, C["l2"])
txt(184, 143, "状态文件：~/.workbuddy/skills/.state/*.json（在 git 仓库外，skill 更新/重装不丢）", 8.6, C["dim"])

# ===== 阶段 1 =====
box(130, 160, 420, 52, "阶段 1 · 问句归一化（必做，检索前）",
    ["① 小白现象词典（106 条） ② 口语问句映射（197 条） ③ 中英术语（112）/ 实战路由（75）",
     "匹配：整句精确 → 滑窗 2~12 字 → 取值按 / → 空格拆多候选词"],
    C["l1bg"], C["l1"], 12, 9.5)
arrow(340, 212, 340, 228, C["line"])
txt(348, 225, "命中「需澄清」→ 先反问用户，不硬答不联网", 9.2, C["l3"])

# ===== 阶段 2：L1 =====
rect(20, 228, 640, 158, "none", C["l1"], 10, 2)
tag(20, 228, 76, "L1 极速", C["l1"], "默认 · 全程离线 · 禁止联网 · ≤300 字")
box(40, 258, 292, 46, "第 1 轮 · 小资产 Grep（~250ms）", ["高频速查 128 / 快捷键 818 / 插件对照", "插件清单 169 / 术语对照"],
    "#ffffff", "#c9d1d9")
box(348, 258, 292, 46, "第 2 轮 · 倒排索引拿页码（~300ms）", ["index_terms.txt 36711 词（每词一行）", "→ 按页码精读 21.1原文检索.txt 局部"],
    "#ffffff", "#c9d1d9")
box(40, 314, 292, 30, "开发类直通（不走前两轮）", ["Grep 官方开发文档蒸馏.md"],
    C["l1bg"], C["l1"], 10.5, 9.5)
box(348, 314, 292, 30, "⚠ 禁用 index.json（71万字符单行）", ["用 index_terms.txt 替代"],
    "#ffebe9", C["l3"], 10.5, 9.5)
box(40, 354, 600, 24, "✓ 能给出完整步骤 → 直接答（结论 + 1/2/3 步骤 + 快捷键 Mac/Win + 仅Studio 标注）",
    [], C["okbg"], C["ok"], 10.5, 9.5)

# ===== 阶段 3：升级判定 =====
arrow(340, 386, 340, 404, C["purple"])
rect(20, 404, 640, 92, "none", C["purple"], 10, 2)
tag(20, 404, 92, "升级判定", C["purple"], "双触发源 · 命中任一即升 L2 · 与「是不是追问」无关")
box(40, 434, 292, 50, "A · 本地答不上来", ["① 两轮都没命中", "② 只能给参数、给不出原理"],
    "#f3e8ff", C["purple"], 11, 9.5)
box(348, 434, 292, 50, "B · 用户明确要深入", ["深入类：详细讲讲/为什么/原理", "对比类：对比一下/哪个好　穷尽类：都有哪些"],
    "#f3e8ff", C["purple"], 11, 9.5)
txt(340, 492, "「追问」是辅助信号，只用于答后多给背景 + 篇幅放宽到 400~500 字，本身不触发升级", 9, C["dim"], None, "middle")

# ===== 阶段 4：L2 =====
arrow(340, 496, 340, 514, C["l2"])
rect(20, 514, 640, 106, "none", C["l2"], 10, 2)
tag(20, 514, 76, "L2 深读", C["l2"], "自动升级 · 首次联网 · 篇幅放宽")
box(40, 544, 600, 44, "全文精读 ±50~100 行（中/英对照）",
    ["用 index_terms.txt 定位页码 + chapters.txt 定章节 → 读命中处上下文"],
    C["l2bg"], C["l2"])
box(40, 594, 600, 20, "+ 联网搜索（官方社区 / YouTube / B站）做双重比对，冲突以英文原版 + 官方来源为准", [],
    "#fff8c5", C["l2"], 9.8, 9)

# ===== 阶段 5：L3 =====
arrow(340, 620, 340, 638, C["l3"])
rect(20, 638, 640, 84, "none", C["l3"], 10, 2)
tag(20, 638, 76, "L3 兜底", C["l3"], "手册未覆盖 · 不编造")
box(40, 668, 600, 44, "明说「手册未覆盖」+ 标注「这是外部说法、非手册内容」",
    ["给外部来源链接 + 可执行的排查 / 试错步骤（而不是含糊结论）"],
    C["l3bg"], "#cf222e")

# ===== 阶段 6：输出与回写 =====
arrow(340, 722, 340, 740, C["ok"])
rect(20, 740, 640, 106, "none", C["ok"], 10, 2)
tag(20, 740, 88, "输出与回写", C["ok"], "每次回答都要做")
box(40, 770, 292, 62, "答后必问", ["末行问「要打开手册浏览器？」", "用户确认后才present_files 打开", "（六个 tab，默认不开）"],
    C["okbg"], C["ok"])
box(348, 770, 292, 62, "回写本地资产", ["新问法补进三层词典", "node check-first-run.js --topic \"域-对象\"", "→ 下次同问题在 L1 命中"],
    C["okbg"], C["ok"])

# ===== 维护闭环 =====
arrow(340, 846, 340, 864, C["purple"])
rect(20, 864, 640, 92, "none", C["purple"], 10, 2)
tag(20, 864, 108, "维护闭环", C["purple"], "词典改动后必跑回归")
box(40, 894, 600, 52, "node scripts/hitrate-test.js",
    ["内置 75 条真实问句（A 档术语 37 + B 档白话 38），<95% 报警",
     "另读recentTopics 做真实问句覆盖检查，未命中即提示补词典"],
    "#f3e8ff", C["purple"])

# ===== 检索路由表 =====
txt(20, 984, "检索路由（按问题类型）", 11.5, C["text"], "700")
routes = [
    ("快捷键", "shortcuts.md（818 条 / 14 模块）", "~250ms"),
    ("怎么XXX / 某功能在哪", "高频速查.md 128 条 → 未中则 index_terms.txt 拿页码", "~300ms"),
    ("插件中文名 / 是否 Studio", "Resolve_FX中英对照.md + Fairlight音频插件.md", "~250ms"),
    ("实战技巧（色彩/混音/Fusion/转软件）", "实战术语对照.txt → 油管笔记对应小节", "~300ms"),
    ("有没有免费插件 / 怎么装", "开源插件清单.md（169 项 + 四类安装路径）", "~250ms"),
    ("开发 / 脚本 / API / MCP / DCTL", "官方开发文档蒸馏.md（直达，不联网）", "~300ms"),
    ("都没命中", "index_terms.txt 拿页码 → 全文精读局部（可切中·英）", "~300ms"),
]
y = 1002
for k, v, t in routes:
    txt(24, y, "▸ " + k, 9.8, C["l1"])
    txt(280, y, v, 9.8, C["dim"])
    txt(660, y, t, 9.2, C["ok"], None, "end")
    y += 16

# ===== 为什么 L1 不联网 =====
rect(20, 1128, 640, 72, C["gray"], "#c9d1d9", 10, 1.5)
txt(32, 1146, "为什么 L1 坚决不联网", 11, C["text"], "700")
txt(32, 1163, "本地 Grep 约 250~310ms、返回 KB 级；联网 3~15 秒、返回几十 KB 且可能不通（本机 git push / PyPI 均被代理拦）。", 9.5, C["dim"])
txt(32, 1179, "联网是「查不到时的兜底」，不是加速手段 —— 绝大多数问题本地已覆盖。命中率：术语 100% / 白话 100%。", 9.5, C["dim"])

# ===== 底部 =====
txt(20, 1224, "归一化词典规模（2026-10-05）", 10.5, C["text"], "700")
txt(20, 1242, "小白现象 106 条　·　口语问句 197 条　·　中英术语 112 条　·　实战路由 75 条", 9.8, C["dim"])
txt(20, 1262, "状态文件 ~/.workbuddy/skills/.state/达芬奇21中文操作手册.json（firstRunShown / recentTopics / useCount）", 9.2, C["dim"])
txt(20, 1284, "详细说明见使用思路.md　·　流程图源文件 references/flow-detailed.svg", 9.2, C["dim"])

A("</svg>")
io.open(OUT, "w", encoding="utf-8", newline="\n").write("".join(p))
print("已写入:", OUT, os.path.getsize(OUT), "bytes")
