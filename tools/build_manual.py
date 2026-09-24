#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_manual.py —— 达芬奇 21.1 手册离线数据构建工具

从「汉化 PDF」与「英文原版 PDF」抽取每页文本，生成 4 个产物：
  - 21.1原文检索.txt        （中文全文，带 "===== Page N =====" 页码标记，供 agent Grep）
  - 21.1英文原文检索.txt     （英文原版全文，同格式）
  - manual.json             （中文 {n,t} 数组，注入浏览器用，已转义 < > 与 </）
  - manualEn.json           （英文原版 {n,t} 数组，注入浏览器用）

用法：
  # 抽取中文 + 英文，输出到 skill 的 references/
  python build_manual.py --zh "D:/达芬奇21.1说明书汉化_全本V2.pdf" \
                         --en "D:/Resolve Manual（英文原版）.pdf" \
                         --out "../references"

  # 仅抽取中文（不传 --en 即可）
  python build_manual.py --zh "D:/汉化.pdf" --out "../references"

  # 把已生成的 manual.json / manualEn.json 注入浏览器 HTML（替换 manual/manualEn 段）
  python build_manual.py --inject-html "../references/手册浏览器.html" \
                         --out "../references"

依赖：
  pip install pymupdf        （PyMuPDF，用于 PDF 文本抽取）

说明：
  - 所有输出均为 UTF-8，中文/英文路径均无乱码。
  - manual*.json 的 t 字段已对 < > 与 </ 做转义，可直接内联进 手册浏览器.html
    的 window.DATA 的 "manual" / "manualEn" 数组。
  - 生成后务必运行 validate.py 自检 DATA 合法性（长度一致、JSON 可解析）。
  - 本工具仅供「离线查阅 / 歧义对照」用途；英文原版版权归 Blackmagic Design 所有。
"""

import argparse
import json
import os
import sys

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.stderr.write(
        "缺少依赖 PyMuPDF，请先运行：pip install pymupdf\n"
    )
    sys.exit(2)


def extract_pages(pdf_path):
    """返回每页纯文本列表（按 1-based 页码）。"""
    doc = fitz.open(pdf_path)
    try:
        return [doc[i].get_text("text") for i in range(doc.page_count)]
    finally:
        doc.close()


def safe_text(s):
    """转义 < > 与 </，避免破坏 HTML / 闭合 script。"""
    return s.replace("<", "\\u003c").replace(">", "\\u003e").replace("</", "<\\u002f")


def write_txt(texts, path, header):
    with open(path, "w", encoding="utf-8") as f:
        f.write(header + "\n\n")
        for i, t in enumerate(texts):
            f.write("===== Page %d =====\n" % (i + 1))
            f.write(t)
            if not t.endswith("\n"):
                f.write("\n")


def write_json(texts, path):
    arr = [{"n": i + 1, "t": safe_text(t)} for i, t in enumerate(texts)]
    s = json.dumps(arr, ensure_ascii=False, separators=(",", ":"))
    with open(path, "w", encoding="utf-8") as f:
        f.write(s)


def build(zh_path, en_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    if zh_path:
        print("抽取中文 PDF：%s" % zh_path)
        zh = extract_pages(zh_path)
        print("  中文页数：%d" % len(zh))
        write_txt(zh, os.path.join(out_dir, "21.1原文检索.txt"),
                  "DaVinci Resolve 21.1 官方参考手册（中文汉化，V2）—— 全文 %d 页" % len(zh))
        write_json(zh, os.path.join(out_dir, "manual.json"))
        print("  -> 21.1原文检索.txt / manual.json")
    if en_path:
        print("抽取英文 PDF：%s" % en_path)
        en = extract_pages(en_path)
        print("  英文页数：%d" % len(en))
        write_txt(en, os.path.join(out_dir, "21.1英文原文检索.txt"),
                  "DaVinci Resolve 21.1 Reference Manual (English Original) —— full text, %d pages" % len(en))
        write_json(en, os.path.join(out_dir, "manualEn.json"))
        print("  -> 21.1英文原文检索.txt / manualEn.json")
    print("完成。下一步：运行 validate.py 自检，或用 --inject-html 注入浏览器。")


def inject_html(html_path, out_dir):
    for fn in ("manual.json", "manualEn.json"):
        p = os.path.join(out_dir, fn)
        if not os.path.exists(p):
            sys.stderr.write("缺少 %s，请先抽取。\n" % p)
            sys.exit(1)
    html = open(html_path, encoding="utf-8").read()
    mj = open(os.path.join(out_dir, "manual.json"), encoding="utf-8").read().strip()
    ej = open(os.path.join(out_dir, "manualEn.json"), encoding="utf-8").read().strip()

    start_tag = '"manual":['
    end_tag = '],"plugins"'
    si = html.index(start_tag)
    ei = html.index(end_tag, si)  # 从 manual 起点向后找，保证唯一边界
    new = html[:si] + '"manual":' + mj + ',"manualEn":' + ej + end_tag + html[ei + len(end_tag):]
    open(html_path, "w", encoding="utf-8").write(new)
    print("已注入 manual(%d字节) + manualEn(%d字节) 到 %s" % (len(mj), len(ej), html_path))


def main():
    ap = argparse.ArgumentParser(description="达芬奇 21.1 手册离线数据构建工具")
    ap.add_argument("--zh", help="中文汉化 PDF 路径")
    ap.add_argument("--en", help="英文原版 PDF 路径（可选）")
    ap.add_argument("--out", default="../references", help="输出目录（默认 ../references）")
    ap.add_argument("--inject-html", help="把 manual.json/manualEn.json 注入此 HTML（替换 manual/manualEn 段）")
    args = ap.parse_args()

    if args.inject_html:
        inject_html(args.inject_html, args.out)
        return

    if not args.zh and not args.en:
        ap.error("至少需要 --zh 或 --en 之一（或指定 --inject-html）")
    build(args.zh, args.en, args.out)


if __name__ == "__main__":
    main()
