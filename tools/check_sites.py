#!/usr/bin/env python3
"""링크 접속 검사 + 결과별 분류.

사용법:
  python check_sites.py /tmp/parsed.json -o checked.json --workers 10
  python check_sites.py /tmp/parsed_group.json -o checked.json

분류(status): ok / redirect_loop / http_4xx / http_5xx / dns_error /
  timeout / refused / ssl_error / unknown_error
"""
import argparse
import json
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) schoolnet-atlas/1.0"}


def load_links(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    items = []
    if isinstance(data, list) and data and "results" in (data[0] or {}):
        for g in data:
            for r in g.get("results", []):
                items.append({"query": g.get("query", ""),
                              "title": r.get("title", ""), "link": r.get("link", "")})
    elif isinstance(data, list):
        items = [{"query": r.get("query", ""), "title": r.get("title", ""),
                  "link": r.get("link", "")} for r in data]
    return [i for i in items if i["link"]]


def check(item, timeout):
    url = item["link"]
    t0 = time.time()
    out = dict(item)
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            r.read(65536)
            out.update({"status": "ok", "code": r.status,
                        "final_url": r.url, "secs": round(time.time() - t0, 2)})
    except urllib.error.HTTPError as e:
        code = e.code
        cat = "http_4xx" if 400 <= code < 500 else "http_5xx" if 500 <= code < 600 else "http_error"
        out.update({"status": cat, "code": code,
                    "final_url": e.url, "secs": round(time.time() - t0, 2)})
    except urllib.error.URLError as e:
        reason = e.reason
        if isinstance(reason, socket.gaierror):
            cat = "dns_error"
        elif isinstance(reason, TimeoutError) or "timed out" in str(reason):
            cat = "timeout"
        elif isinstance(reason, ConnectionRefusedError) or "refused" in str(reason).lower():
            cat = "refused"
        elif isinstance(reason, ssl.SSLError) or "ssl" in str(type(reason)).lower() or "certificate" in str(reason).lower():
            cat = "ssl_error"
        else:
            cat = "unknown_error"
        out.update({"status": cat, "code": None, "error": str(reason)[:200],
                    "secs": round(time.time() - t0, 2)})
    except socket.timeout:
        out.update({"status": "timeout", "code": None, "secs": round(time.time() - t0, 2)})
    except Exception as e:
        out.update({"status": "unknown_error", "code": None,
                    "error": f"{type(e).__name__}: {e}"[:200],
                    "secs": round(time.time() - t0, 2)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="parse_results.py 출력 JSON")
    ap.add_argument("-o", "--output", default="checked.json")
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--timeout", type=float, default=15.0)
    args = ap.parse_args()

    items = load_links(args.input)
    print(f"{len(items)}개 검사 시작 (workers={args.workers})", file=sys.stderr)
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(check, it, args.timeout): it for it in items}
        for i, fut in enumerate(as_completed(futs), 1):
            results.append(fut.result())
            if i % 50 == 0:
                print(f"{i}/{len(items)}...", file=sys.stderr)

    summary = {}
    for r in results:
        summary[r["status"]] = summary.get(r["status"], 0) + 1
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "results": results}, f, ensure_ascii=False, indent=2)
    print(f"분류: {json.dumps(summary, ensure_ascii=False)}", file=sys.stderr)
    print(f"저장: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
