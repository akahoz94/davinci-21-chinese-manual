# 达芬奇 21 中文操作手册（DaVinci 21 Chinese Manual）

一个**离线、自包含**的 DaVinci Resolve 21.1 中文操作手册 —— 既是给 AI 助手（WorkBuddy 等）检索用的 skill，也是给人类直接浏览/搜索的可视化网页。

> 原文汉化：**@谜一样的剪辑师**
> 收集整合：**@一个成熟的剪辑猿**

---

## ✨ 功能

单文件网页浏览器（`references/手册浏览器.html`，离线可用，无需联网/无需服务器），包含三个标签页：

| 标签页 | 内容 | 数据量 |
|--------|------|--------|
| ⌨ **快捷键速查** | 按模块分组的快捷键，支持关键词搜索 + 模块筛选 | 816 条 / 14 模块 |
| 🔍 **功能检索** | 21.1 官方手册全文搜索（4351 页），命中可阅读整页 | 4351 页 |
| 🧩 **内置插件中英对比** | Resolve FX 特效 + Fairlight 音频插件的中英对照，含「是否 Studio 专属」 | 218 条（FX 154 + Fairlight 64） |

快捷键以 macOS 惯例（⌘ Command / ⌥ Option）展示，Windows / Linux 用 Ctrl 替 ⌘、Alt 替 ⌥。

## 📦 安装（作为 AI Skill 使用）

把本仓库内容放进你的 WorkBuddy skills 目录：

```bash
# 方式一：直接复制到 skills 目录
cp -r davinci-21-chinese-manual "$HOME/.workbuddy/skills/达芬奇21中文操作手册"

# 方式二：git clone
git clone https://github.com/akahoz94/davinci-21-chinese-manual.git \
  "$HOME/.workbuddy/skills/达芬奇21中文操作手册"
```

重启 / 新开对话后，提到达芬奇相关问题时该 skill 会被自动加载；需要可视化浏览时，AI 会调用 `手册浏览器.html`。

## 🌐 仅作网页使用（不用 AI）

直接双击 `references/手册浏览器.html` 用浏览器打开即可，全部数据已内联，离线可用。

## 📁 目录结构

```
达芬奇21中文操作手册/
├── SKILL.md                  # AI 检索路由与规范
├── README.md                # 本文件
├── LICENSE                  # MIT 开源协议
└── references/
    ├── 手册浏览器.html        # 自包含可视化浏览器（离线）
    ├── shortcuts.md          # 快捷键速查（816 条）
    ├── Resolve_FX中英对照.md  # Resolve FX 特效中英对照（154 条）
    └── Fairlight音频插件.md   # Fairlight 音频插件中英对照（64 条）
```

## 📄 数据来源与版权

- 手册正文翻译自 **DaVinci Resolve 21.1 官方参考手册**，原文汉化版权归 **@谜一样的剪辑师** 所有。
- 本 skill 的代码、整合与网页构建版权归 **@一个成熟的剪辑猿** 所有，以 **MIT 协议** 开源（见 `LICENSE`）。
- 快捷键跨版本基本通用；如与你所用的具体版本有出入，以软件内「帮助」为准。

欢迎提 Issue / PR 完善对照表与快捷键。
