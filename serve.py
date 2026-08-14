#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本地预览服务器。

把 modellens/site/ 目录作为静态站点跑起来，方便本地查看每日报告与落地页，
无需任何外部服务。

用法：
  python serve.py                # 默认端口 8000
  python serve.py --port 9000
然后浏览器打开 http://localhost:8000/
"""
import argparse
import http.server
import os
import socketserver
from functools import partial

SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "site")


def main():
    ap = argparse.ArgumentParser(description="模型筛本地预览服务器")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--host", default="127.0.0.1")
    a = ap.parse_args()

    os.makedirs(SITE, exist_ok=True)
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=SITE)
    with socketserver.TCPServer((a.host, a.port), handler) as httpd:
        url = f"http://{a.host}:{a.port}/"
        print(f"模型筛本地预览：{url}")
        print(f"（目录：{SITE}） ｜ Ctrl+C 退出")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n已停止。")


if __name__ == "__main__":
    main()
