# API 키 발급 방법 (search_links.py용)

공식 API만 사용. 키 없이 긁지 않음.

## 1. Google (Custom Search JSON API)

1. https://console.cloud.google.com/ → 프로젝트 생성(또는 선택)
2. API 및 서비스 > 라이브러리 → `Custom Search API` 사용 설정
3. 사용자 인증 정보 > 사용자 인증 정보 만들기 > API 키 → `GOOGLE_API_KEY` 복사
   - 공식 문서: https://developers.google.com/custom-search/v1/overview?hl=ko (하루 100건 무료)
4. https://programmablesearchengine.google.com/ → 검색엔진 만들기
   - `전체 웹 검색` 켜기 (특정 사이트로 한정하지 않음)
   - 생성 후 `검색 엔진 ID` 복사 → `GOOGLE_CX`
5. 적용:
   export GOOGLE_API_KEY="..."
   export GOOGLE_CX="..."

## 2. Naver (검색 API)

1. https://developers.naver.com/ 로그인 → Application > 애플리케이션 등록
2. 사용 API에서 `검색` 체크 → 등록
3. 내 애플리케이션에서 `Client ID` / `Client Secret` 복사
   - 호출 시 헤더 `X-Naver-Client-Id` / `X-Naver-Client-Secret` 사용
   - 참고: https://developers.naver.com/docs/serviceapi/search/encyclopedia/encyclopedia.md (사전 준비 사항 부분)
4. 적용:
   export NAVER_CLIENT_ID="..."
   export NAVER_CLIENT_SECRET="..."

## 3. Serper (구글 결과 대행, 권장)

신규 Programmable Search Engine이 전체 웹 불가라 구글 전체 검색용으로 권장.

1. https://serper.dev/ 가입 → 대시보드에서 API 키 복사 (신규 2,500건 무료, 카드 불필요)
2. 적용:
   export SERPER_API_KEY="..."
3. 실행:
   python tools/search_links.py tools/keywords.example.txt -n 5 --engine serper -o results.json
   - n=10까지 1크레딧, 11~100은 2크레딧 소모라 기본 5~10 권장

## 4. 실행 예시

  python tools/search_links.py tools/keywords.example.txt -n 5 --engine both -o results.json
  python tools/search_links.py tools/keywords.example.txt -n 5 --engine naver -o results.csv

## 주의

- 키는 코드·깃에 넣지 말고 환경변수만 사용
- 403이 나면 Naver는 API 권한관리에서 검색 체크 여부, Google은 API 사용 설정 + CX 확인
