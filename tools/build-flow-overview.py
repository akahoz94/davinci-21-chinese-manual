import io, os

REF = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references"))
OUT = os.path.join(REF, "flow-overview.svg")

C = {"text": "#1f2328", "dim": "#656d76", "line": "#d0d7de",
     "l1": "#0969da", "l2": "#bf8700", "l3": "#cf222e", "ok": "#1a7f37",
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

def box(x, y, w, h, title, lines, fill, stroke, tfs=12, lfs=10):
    rect(x, y, w, h, fill, stroke)
    txt(x + 11, y + 18, title, tfs, C["text"], "600")
    for i, t in enumerate(lines):
        txt(x + 11, y + 33 + i * 13, t, lfs, C["dim"])

def arrow(x1, y1, x2, y2, color, label=None, lx=None, ly=None):
    A(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="1.5" marker-end="url(#ar)"/>')
    if label:
        txt(lx if lx else (x1+x2)//2, ly if ly else (y1+y2)//2 - 4, label, 9.5, C["dim"], None, "middle")

def tag(x, y, w, label, color, sub):
    rect(x, y, w, 22, color, color, 6)
    txt(x + w/2, y + 15, label, 11, "#fff", "700", "middle")
    txt(x + w + 11, y + 15, sub, 9.5, color)

W, H = 680, 780
A(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img">')
A('<title>达芬奇21中文操作手册 · 运行逻辑速览（首次判定 + 双触发源三态递进）</title>')
A('<desc>每次激活先判是否首次：读状态文件，firstRunShown=true 则跳过引导直接问答（零开销）。提问后先过三层问句归一化词典，再走三态递进：L1 极速本地检索（默认、离线）、L2 深读（本地答不上来或用户明确要深入）、L3 兜底（明说手册未覆盖）。答后把新问法回写词典与主题记录，下次走 L1 命中。</desc>')
A('<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#656d76"/></marker></defs>')
rect(0, 0, W, H, "#ffffff", "#ffffff", 0, 0)

txt(340, 24, "运行逻辑速览 · 首次判定 + 三态递进", 14.5, C["text"], "700", "middle")
txt(340, 41, "本地查得到就用本地，查不到才联网 · 首次调用约 300ms", 10, C["dim"], None, "middle")

# ===== 阶段 0：首次判定 =====
rect(20, 54, 640, 74, C["gray"], "#c9d1d9", 10, 1.5)
txt(32, 70, "阶段 0 · 首次使用判定（跨会话只做一次）", 11.5, C["text"], "700")
box(32, 78, 300, 40, "读状态文件", ["check-first-run.js → isFirstRun"],
    "#ffffff", "#c9d1d9", 11, 9.5)
box(348, 78, 300, 40, "false → 直接问答", ["不弹图· 不读 SVG（零开销）"],
    C["okbg"], C["ok"], 11, 9.5)
arrow(336, 98, 346, 98, C["ok"])

# true 分支向下
arrow(182, 118, 182, 132, C["l2"])
txt(190, 129, "true → 首次：展示速览图 → --mark 落盘（此后不再弹）", 9.5, C["l2"])

# ===== 归一化 =====
box(140, 132, 400, 44, "第 1 步 · 问句归一化（必做）",
    ["三层词典：① 小白现象 ② 口语问句 ③ 中英/章节映射"],
    C["l1bg"], C["l1"], 12, 9.5)
arrow(340, 176, 340, 192, C["line"])
txt(350, 188, "「需澄清」→ 先反问，不硬答不联网", 9.5, C["l3"])

# ===== L1 =====
rect(20, 192, 640, 118, "none", C["l1"], 10, 2)
tag(20, 192, 76, "L1 极速", C["l1"], "默认 · 全程离线 · 约 300ms")
box(40, 222, 290, 44, "第 1 轮 · 小资产 Grep", ["速查/ 快捷键 / 插件对照 / 术语表"],
    "#ffffff", "#c9d1d9", 11, 9.5)
box(350, 222, 290, 44, "第 2 轮 · 倒排索引拿页码", ["36711 词 → 精读手册局部"],
    "#ffffff", "#c9d1d9", 11, 9.5)
box(40, 276, 600, 24, "✓ 能给出完整步骤 → 直接答（≤300 字，Mac/Win 双写）",
    [], C["okbg"], C["ok"], 11, 9.5)

# L1 出口箭头到 L2
arrow(340, 310, 340, 336, C["l2"])

# ===== 升级判定 =====
rect(20, 336, 640, 76, "none", "#8250df", 10, 2)
tag(20, 336, 108, "升级判定", "#8250df", "双触发源 · 命中任一即升 L2（与「是不是追问」无关）")
box(40, 366, 292, 36, "A 本地答不上来", ["两轮未命中 / 只给参数给不出原理"],
    "#f3e8ff", "#8250df", 11, 9.5)
box(348, 366, 292, 36, "B 用户明确要深入", ["详细讲讲/ 为什么 / 对比一下"],
    "#f3e8ff", "#8250df", 11, 9.5)

# ===== L2 =====
arrow(600, 412, 600, 428, C["l2"])
rect(20, 428, 640, 88, "none", C["l2"], 10, 2)
tag(20, 428, 76, "L2 深读", C["l2"], "自动升级 · 首次联网 · 篇幅放宽")
box(40, 458, 600, 46, "全文精读 ±50~100 行（中/英对照） + 联网搜索双重比对",
    ["冲突时以 Blackmagic 英文原版 + 官方来源为准"],
    C["l2bg"], C["l2"], 11.5, 9.5)
arrow(340, 504, 340, 520, C["l3"])

# ===== L3 =====
rect(20, 520, 640, 66, "none", C["l3"], 10, 2)
tag(20, 520, 76, "L3 兜底", C["l3"], "手册未覆盖 · 不编造")
box(40, 548, 600, 28, "明说「手册未覆盖」+ 标注「外部说法」+ 给可执行试错步骤",
    [], C["l3bg"], "#cf222e", 11, 9.5)

# ===== 回流 =====
arrow(340, 586, 340, 604, C["ok"])
box(40, 604, 600, 44, "答后回写：把新问法补进三层词典 + 记录本轮主题（--topic）",
    ["下次同样问题在 L1 就命中 —— 命中率持续上升"],
    C["okbg"], C["ok"], 11.5, 9.5)

# ===== 底部：路由表 =====
txt(20, 670, "检索路由（按问题类型）", 11, C["text"], "600")
routes = [("快捷键", "shortcuts.md"),
          ("怎么XXX / 功能在哪", "高频速查 → index_terms 拿页码"),
          ("实战技巧（色彩/混音/Fusion）", "术语对照 → 油管笔记小节"),
          ("免费插件 / 怎么装", "开源插件清单 169 项"),
          ("开发 / 脚本 / API / MCP", "开发文档蒸馏（直达，不联网）")]
y = 687
for k, v in routes:
    txt(24, y, "▸ " + k, 9.5, C["l1"])
    txt(196, y, v, 9.5, C["dim"])
    y += 15

A("</svg>")
io.open(OUT, "w", encoding="utf-8", newline="\n").write("".join(p))
print("已写入:", OUT, os.path.getsize(OUT), "bytes")
