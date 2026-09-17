#!/usr/bin/env python3
"""키워드 파일 -> Google/Naver 상위 n개 링크 수집 (공식 API 사용).

사용법:
  python search_links.py keywords.txt -n 5 --engine both -o results.json
  python search_links.py keywords.txt -n 5 --engine naver -o results.csv

필요 환경변수:
  Google: GOOGLE_API_KEY, GOOGLE_CX (단, 2026-01 이후 신규 엔진은 전체 웹 불가)
  Naver : NAVER_CLIENT_ID, NAVER_CLIENT_SECRET
  Serper: SERPER_API_KEY (구글 결과 대행, 신규 2,500건 무료)

keywords.txt: 한 줄에 키워드 하나 (빈 줄/# 주석 무시)
"""
import argparse
import csv
import hashlib
import json
import os
import sys
import time
import urllib.parse
import urllib.request


def read_keywords(path):
    kws = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            kws.append(line)
    return kws


def http_get_json(url, headers=None, timeout=15):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def http_post_json(url, payload, headers=None, timeout=15):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers or {}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def search_serper(query, n, api_key):
    # serper.dev 구글 SERP 대행. 1크레딧당 최대 10개, n>10이면 2크레딧
    data = http_post_json(
        "https://google.serper.dev/search",
        {"q": query, "num": min(max(n, 1), 100)},
        {"X-API-KEY": api_key, "Content-Type": "application/json"},
    )
    out = []
    for item in (data.get("organic") or [])[:n]:
        out.append({
            "engine": "serper-google", "query": query,
            "title": item.get("title", ""),
            "link": item.get("link", ""),
        })
    return out


def cache_path(cache_dir, engine, query, n):
    h = hashlib.sha256(f"{engine}|{query}|{n}".encode("utf-8")).hexdigest()[:16]
    safe = "".join(c if c.isalnum() else "_" for c in query)[:30]
    return os.path.join(cache_dir, f"{engine}_{safe}_{h}.json")


def cache_get(path, ttl_days):
    if not os.path.exists(path):
        return None
    age = time.time() - os.path.getmtime(path)
    if age > ttl_days * 86400:
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def cache_set(path, data):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def cached_search(engine, query, n, fn, cache_dir, ttl_days, use_cache):
    if not use_cache:
        return fn()
    p = cache_path(cache_dir, engine, query, n)
    hit = cache_get(p, ttl_days)
    if hit is not None:
        print(f"[cache] '{query}' ({engine}) 재사용", file=sys.stderr)
        return hit
    out = fn()
    cache_set(p, out)
    return out


def search_google(query, n, api_key, cx):
    # Custom Search API는 1회 최대 10개
    out = []
    start = 1
    while len(out) < n:
        num = min(10, n - len(out))
        q = urllib.parse.urlencode({
            "key": api_key, "cx": cx, "q": query,
            "num": num, "start": start,
        })
        data = http_get_json(f"https://www.googleapis.com/customsearch/v1?{q}")
        for item in data.get("items", []):
            out.append({
                "engine": "google", "query": query,
                "title": item.get("title", ""),
                "link": item.get("link", ""),
            })
        if "nextPage" not in str(data.get("queries", {})) or not data.get("items"):
            break
        start += num
        time.sleep(1)
    return out[:n]


def search_naver(query, n, client_id, client_secret):
    # webkr display 최대 100
    q = urllib.parse.urlencode({
        "query": query, "display": min(max(n, 1), 100), "start": 1,
    })
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }
    data = http_get_json(f"https://openapi.naver.com/v1/search/webkr.json?{q}", headers)
    out = []
    for item in data.get("items", [])[:n]:
        # naver webkr은 title에 <b> 태그 포함 가능
        title = item.get("title", "").replace("<b>", "").replace("</b>", "")
        out.append({
            "engine": "naver", "query": query,
            "title": title, "link": item.get("link", ""),
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("keyword_file", help="한 줄에 키워드 하나")
    ap.add_argument("-n", type=int, default=5, help="키워드당 상위 n개 (기본 5)")
    ap.add_argument("--engine", choices=["google", "naver", "serper", "both", "all"], default="both")
    ap.add_argument("-o", "--output", default="-", help="출력 파일 (.json/.csv, -는 stdout)")
    ap.add_argument("--delay", type=float, default=1.0, help="키워드 간 대기 초")
    ap.add_argument("--cache-dir", default=".search_cache", help="결과 캐시 디렉토리 (기본 .search_cache)")
    ap.add_argument("--cache-ttl", type=float, default=7.0, help="캐시 유효 일수 (기본 7일)")
    ap.add_argument("--no-cache", action="store_true", help="캐시 사용 안 함")
    args = ap.parse_args()

    kws = read_keywords(args.keyword_file)
    if not kws:
        print("키워드가 없음", file=sys.stderr)
        sys.exit(1)

    need_google = args.engine in ("google", "both", "all")
    need_naver = args.engine in ("naver", "both", "all")
    need_serper = args.engine in ("serper", "all")
    g_key = os.getenv("GOOGLE_API_KEY", "")
    g_cx = os.getenv("GOOGLE_CX", "")
    n_id = os.getenv("NAVER_CLIENT_ID", "")
    n_sec = os.getenv("NAVER_CLIENT_SECRET", "")
    s_key = os.getenv("SERPER_API_KEY", "")
    if need_google and (not g_key or not g_cx):
        print("GOOGLE_API_KEY/GOOGLE_CX 필요", file=sys.stderr)
        sys.exit(2)
    if need_naver and (not n_id or not n_sec):
        print("NAVER_CLIENT_ID/NAVER_CLIENT_SECRET 필요", file=sys.stderr)
        sys.exit(2)
    if need_serper and not s_key:
        print("SERPER_API_KEY 필요", file=sys.stderr)
        sys.exit(2)

    rows = []
    use_cache = not args.no_cache
    for kw in kws:
        try:
            if need_google:
                rows.extend(cached_search(
                    "google", kw, args.n,
                    lambda kw=kw: search_google(kw, args.n, g_key, g_cx),
                    args.cache_dir, args.cache_ttl, use_cache))
        except Exception as e:
            print(f"[google] '{kw}' 실패: {e}", file=sys.stderr)
        try:
            if need_naver:
                rows.extend(cached_search(
                    "naver", kw, args.n,
                    lambda kw=kw: search_naver(kw, args.n, n_id, n_sec),
                    args.cache_dir, args.cache_ttl, use_cache))
        except Exception as e:
            print(f"[naver] '{kw}' 실패: {e}", file=sys.stderr)
        try:
            if need_serper:
                rows.extend(cached_search(
                    "serper", kw, args.n,
                    lambda kw=kw: search_serper(kw, args.n, s_key),
                    args.cache_dir, args.cache_ttl, use_cache))
        except Exception as e:
            print(f"[serper] '{kw}' 실패: {e}", file=sys.stderr)
        time.sleep(args.delay)

    if args.output == "-":
        json.dump(rows, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    elif args.output.endswith(".csv"):
        with open(args.output, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["engine", "query", "title", "link"])
            w.writeheader()
            w.writerows(rows)
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f"{len(rows)}건 저장: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
