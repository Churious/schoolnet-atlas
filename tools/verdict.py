#!/usr/bin/env python3
"""checked_school.json -> 막힘/열림 판정 + 브라우저 대조 명단.

사용법:
  python verdict.py results/school-run-20260917/checked_school.json -o results/school-run-20260917/

생성: verdict.json (전체 판정), browser_checklist.md (대조용 명단)
판정: blocked(차단 확실: dns/timeout/TLS킬) / allowed(ok) /
       unclear(http_4xx 등 사이트 자체 문제 가능)
"""
import argparse
import json
import os

BLOCKED = {"dns_error", "timeout", "ssl_error", "refused"}
UNCLEAR = {"http_4xx", "http_5xx", "http_error", "unknown_error"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--outdir", default=".")
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)
    results = data["results"] if isinstance(data, dict) else data

    verdicts = []
    for r in results:
        st = r.get("status", "")
        if st == "ok":
            v = "allowed"
        elif st in BLOCKED:
            v = "blocked"
        else:
            v = "unclear"
        verdicts.append({"query": r.get("query"), "title": r.get("title"),
                         "link": r.get("link"), "check_status": st,
                         "verdict": v,
                         "evidence": r.get("error") or f'code={r.get("code")}'})

    blocked = [v for v in verdicts if v["verdict"] == "blocked"]
    unclear = [v for v in verdicts if v["verdict"] == "unclear"]
    allowed = [v for v in verdicts if v["verdict"] == "allowed"]

    os.makedirs(args.outdir, exist_ok=True)
    with open(os.path.join(args.outdir, "verdict.json"), "w", encoding="utf-8") as f:
        json.dump({"summary": {"blocked": len(blocked), "allowed": len(allowed),
                               "unclear": len(unclear)},
                   "verdicts": verdicts}, f, ensure_ascii=False, indent=2)

    lines = ["# 브라우저 대조 명단",
             "",
             "학교PC 브라우저에서 직접 열어 O(열림)/X(차단) 표시.",
             "기준: 차단 안내문 또는 ERR_CONNECTION_CLOSED → X.",
             ""]
    lines.append("## 차단 의심 (python에서 막힘)")
    for v in blocked:
        lines.append(f"- [ ] X/O `{v['link']}` ({v['query']})")
    lines += ["", "## 애매함 (http 오류, 사이트 문제 가능)"]
    for v in unclear:
        lines.append(f"- [ ] X/O `{v['link']}` ({v['query']})")
    with open(os.path.join(args.outdir, "browser_checklist.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"blocked {len(blocked)} / allowed {len(allowed)} / unclear {len(unclear)}")


if __name__ == "__main__":
    main()
