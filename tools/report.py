#!/usr/bin/env python3
"""checked.json -> 한눈에 보는 HTML 리포트.

사용법:
  python report.py /tmp/checked.json -o /tmp/report.html
"""
import argparse
import html
import json

COLORS = {
    "ok": "#16a34a", "http_4xx": "#f59e0b", "http_5xx": "#ef4444",
    "http_error": "#ef4444", "dns_error": "#dc2626", "timeout": "#dc2626",
    "refused": "#dc2626", "ssl_error": "#eab308", "unknown_error": "#6b7280",
    "redirect_loop": "#eab308",
}

ORDER = ["ok", "http_4xx", "http_5xx", "http_error", "dns_error",
         "timeout", "refused", "ssl_error", "redirect_loop", "unknown_error"]


def esc(s):
    return html.escape(str(s or ""), quote=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="check_sites.py 출력 JSON")
    ap.add_argument("-o", "--output", default="report.html")
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)
    summary, results = data.get("summary", {}), data.get("results", [])
    total = len(results)

    cards = []
    for st in ORDER:
        n = summary.get(st, 0)
        if not n and st != "ok":
            continue
        c = COLORS.get(st, "#6b7280")
        cards.append(
            f'<div class="card" style="border-top:4px solid {c}">'
            f'<div class="num">{n}</div><div class="lbl">{esc(st)}</div></div>')

    rows = []
    for r in sorted(results, key=lambda x: (x.get("status", ""), x.get("query", ""))):
        st = r.get("status", "")
        c = COLORS.get(st, "#6b7280")
        code = r.get("code") if r.get("code") is not None else "-"
        extra = esc(r.get("error") or r.get("final_url") or "")
        rows.append(
            f'<tr data-status="{esc(st)}">'
            f'<td><span class="badge" style="background:{c}">{esc(st)}</span></td>'
            f'<td>{esc(r.get("query"))}</td>'
            f'<td><a href="{esc(r.get("link"))}" target="_blank" rel="noopener">{esc(r.get("title"))}</a>'
            f'<div class="url">{esc(r.get("link"))}</div></td>'
            f'<td>{esc(code)}</td><td>{esc(r.get("secs"))}s</td>'
            f'<td class="extra">{extra}</td></tr>')

    statuses = sorted({r.get("status", "") for r in results})
    opts = ['<option value="">전체 상태</option>'] + [
        f'<option value="{esc(s)}">{esc(s)} ({summary.get(s, 0)})</option>' for s in statuses]

    page = f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>schoolnet-atlas 검사 리포트 ({total}건)</title>
<style>
body{{font-family:system-ui,sans-serif;margin:0;background:#f3f4f6;color:#111}}
.wrap{{max-width:1100px;margin:0 auto;padding:24px}}
.cards{{display:flex;flex-wrap:wrap;gap:12px;margin:16px 0}}
.card{{background:#fff;border-radius:10px;padding:12px 18px;min-width:110px;box-shadow:0 1px 3px #0001}}
.num{{font-size:28px;font-weight:700}}.lbl{{font-size:13px;color:#555}}
.bar{{display:flex;flex-wrap:wrap;gap:10px;margin:16px 0;position:sticky;top:0;background:#f3f4f6;padding:10px 0}}
input,select{{padding:8px 12px;border:1px solid #ccc;border-radius:8px;font-size:14px}}
table{{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden}}
th,td{{padding:10px;border-bottom:1px solid #eee;text-align:left;font-size:14px;vertical-align:top}}
th{{background:#111827;color:#fff}}
.badge{{color:#fff;font-size:12px;padding:2px 8px;border-radius:99px;white-space:nowrap}}
.url{{font-size:12px;color:#666;word-break:break-all}}
.extra{{font-size:12px;color:#666;max-width:220px;word-break:break-all}}
a{{color:#1d4ed8;text-decoration:none}}a:hover{{text-decoration:underline}}
</style></head><body><div class="wrap">
<h1>검사 리포트 <small>({total}건)</small></h1>
<div class="cards">{''.join(cards)}</div>
<div class="bar">
<input id="q" placeholder="검색 (제목/쿼리/URL)" style="flex:1;min-width:200px">
<select id="f">{''.join(opts)}</select>
</div>
<table><thead><tr><th>상태</th><th>쿼리</th><th>제목 / URL</th><th>코드</th><th>시간</th><th>비고</th></tr></thead>
<tbody id="tb">{''.join(rows)}</tbody></table>
<script>
const q=document.getElementById('q'),f=document.getElementById('f'),tb=document.getElementById('tb');
function filt(){{
const t=q.value.toLowerCase(),s=f.value;
for(const r of tb.rows){{
const st=r.dataset.status;
const okS=!s||st===s;
const okT=!t||r.innerText.toLowerCase().includes(t);
r.style.display=(okS&&okT)?'':'none';
}}}}
q.oninput=filt;f.onchange=filt;
</script></div></body></html>"""

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"리포트: {args.output} ({total}건)", )


if __name__ == "__main__":
    main()
