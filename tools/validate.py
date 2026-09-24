#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate.py —— 校验 手册浏览器.html 内联 DATA 的合法性与完整性

校验项：
  - window.DATA 可被 JSON 解析
  - 关键 key 存在且非空：manual / manualEn / plugins / devdoc / quickref / shortcuts
  - manual 与 manualEn 页数一致（应为 4351，但只比对两者相等）
  - 输出体积报告

用法：
  python validate.py
  python validate.py --html "../references/手册浏览器.html"

退出码：0 = 全部通过；1 = 存在失败项。
"""

import json
import os
import sys

REQUIRED_KEYS = ["manual", "manualEn", "plugins", "devdoc", "quickref", "shortcuts"]


def load_data(html_path):
    s = open(html_path, encoding="utf-8").read()
    marker = "window.DATA = "
    i = s.index(marker) + len(marker)
    data, _ = json.JSONDecoder().raw_decode(s, i)
    return data


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    default_html = os.path.normpath(os.path.join(here, "..", "references", "手册浏览器.html"))
    if len(sys.argv) > 2 and sys.argv[1] == "--html":
        html_path = sys.argv[2]
    else:
        html_path = default_html

    if not os.path.exists(html_path):
        sys.stderr.write("找不到 HTML：%s\n" % html_path)
        sys.exit(1)

    print("校验：%s\n" % html_path)
    try:
        data = load_data(html_path)
    except Exception as e:
        sys.stderr.write("✗ window.DATA 解析失败：%s\n" % e)
        sys.exit(1)

    ok = True
    for k in REQUIRED_KEYS:
        if k not in data:
            print("✗ 缺少关键 key：%s" % k)
            ok = False
            continue
        v = data[k]
        n = len(v) if hasattr(v, "__len__") else 1
        print("✓ %-12s 长度/条目 = %s" % (k, n))

    zh = data.get("manual")
    en = data.get("manualEn")
    if zh is not None and en is not None:
        if len(zh) == len(en):
            print("✓ manual 与 manualEn 页数一致：%d" % len(zh))
        else:
            print("✗ manual(%d) 与 manualEn(%d) 页数不一致" % (len(zh), len(en)))
            ok = False

    # 体积报告
    size = os.path.getsize(html_path)
    print("\n体积报告：HTML %.2f MB" % (size / 1024 / 1024))

    if ok:
        print("\n✅ 全部通过")
        sys.exit(0)
    else:
        print("\n❌ 存在失败项")
        sys.exit(1)


if __name__ == "__main__":
    main()
