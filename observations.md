# 관찰 기록

## 확정 사항 (2026-09-17 학교PC 실측)

- 차단 솔루션: Somansa Integrated Network Agent (HTTP 응답 Server 헤더에서 확인)
- 근거 문구: 교육부 정보보안 기본지침 제47조 (게임, 음란, 도박 등 업무와 무관한 사이트)
- 문의처 표기: 충청남도교육청교육과정평가정보원 (041-640-1922)
- DNS: 정상 (KT DNS, 실제 IP 응답. 변조 없음)
- HTTP(80): 프록시가 가로채 차단 페이지 반환
- HTTPS(443): TLS 핸드셰이크 단계에서 연결 끊김 (차단 페이지 없음, ERR_CONNECTION_CLOSED)
- 기준 추정: 카테고리 기반 (게임·VPN·프록시·웹툰). 같은 게임 카테고리도 poki.com은 허용, crazygames는 차단 → 도메인별 허용/차단 목록 병행 추정

## 실측 요약 (331건, 학교PC)

- ok 267, TLS차단 38, 타임아웃 9, DNS실패 6, http_4xx 9, http_error 2
- 상세: results/school-run-20260917/checked_school.json, report_school.html

| 날짜 | 사이트(도메인만) | 카테고리 | nslookup 결과 요약 | curl/브라우저 결과 | 차단 페이지 유무 | 비고 |
|------|------------------|----------|--------------------|--------------------|------------------|------|
| 2026-09-17 | www.crazygames.com | 게임 | 정상 IP (Cloudflare) | http: 차단 페이지 / https: 연결 끊김 | http만 유 | 소만사 확인 계기 |
| 2026-09-17 | www.proxysite.com | 프록시 | 정상 IP | https 연결 끊김 | 무 | |
| 2026-09-17 | machugi.io | 게임 | 집과 동일 IP | 집 200 OK / 학교 TLS 실패 | 무 | SNI 차단 대조 사례 |
| 2026-09-17 | poki.com | 게임 | - | 브라우저 정상 접속 | 무 | 같은 카테고리인데 허용 (예외) |
