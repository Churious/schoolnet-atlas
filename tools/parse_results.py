#!/usr/bin/env python3
"""검색 결과(JSON/CSV) -> {query, title, link} 깔끔한 JSON으로 정리.

사용법:
  python parse_results.py /tmp/serper_full.json -o parsed.json
  python parse_results.py results.csv -o parsed.json --dedupe
  python parse_results.py /tmp/serper_full.json --group -o by_query.json
"""
import argparse
import csv
import html
import json
import re
import sys


def clean_title(t):
    t = re.sub(r"<[^>]+>", "", t or "")
    return html.unescape(t).strip()


def load_rows(path):
    if path.endswith(".csv"):
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    else:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        rows = data if isinstance(data, list) else data.get("results", data)
    out = []
    for r in rows:
        out.append({
            "query": (r.get("query") or "").strip(),
            "title": clean_title(r.get("title")),
            "link": (r.get("link") or "").strip(),
        })
    return [r for r in out if r["link"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="search_links.py 출력 (.json/.csv)")
    ap.add_argument("-o", "--output", default="-")
    ap.add_argument("--dedupe", action="store_true", help="링크 중복 제거 (첫 등장 유지)")
    ap.add_argument("--group", action="store_true", help="쿼리별 묶음 {query, results:[{title,link}]}")
    args = ap.parse_args()

    rows = load_rows(args.input)
    if args.dedupe:
        seen, uniq = set(), []
        for r in rows:
            if r["link"] not in seen:
                seen.add(r["link"])
                uniq.append(r)
        rows = uniq

    if args.group:
        grouped, order = {}, []
        for r in rows:
            if r["query"] not in grouped:
                grouped[r["query"]] = []
                order.append(r["query"])
            grouped[r["query"]].append({"title": r["title"], "link": r["link"]})
        out = [{"query": q, "results": grouped[q]} for q in order]
    else:
        out = rows

    text = json.dumps(out, ensure_ascii=False, indent=2)
    if args.output == "-":
        sys.stdout.write(text + "\n")
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    print(f"{len(rows)}건 정리: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
