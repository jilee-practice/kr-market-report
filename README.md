# kr-market-report

매일 아침 국내/국외 증시 지표를 수집해 카드형 인포그래픽 이미지를 만들고 이메일로 발송하는 파이프라인.

## 파이프라인 (2단계)

이 리포트는 스크립트가 수치를 "해석"하지 않는다 — 해석(서술)은 매일 이 파이프라인을 실행하는
**클라우드 예약 Claude 에이전트**가 수집된 수치를 보고 직접 작성한다. 그래서 별도 LLM API 키가 필요 없다.

1. **데이터 수집**: `python3 -m scripts.collect_data [--date YYYY-MM-DD]`
   FRED(미국 금리) / EIA(유가) / 한국수출입은행(환율) / yfinance(KOSPI·KOSDAQ, 미국 지수, 관심 종목)를
   조회해 `data/market_data_<date>.json` 으로 저장한다.

   KOSPI/KOSDAQ은 원래 KIS Open API(`scripts/kis_client.py`)로 받았지만, 클라우드 예약 에이전트
   환경에서 KIS가 쓰는 비표준 포트(9443)가 아웃바운드 프록시에 막혀 yfinance(`^KS11`/`^KQ11`)로
   대체했다. KIS 접속이 가능한 환경(로컬 등)에서는 `kis_client.py`를 직접 써도 된다.

2. **해석 작성**: 에이전트가 `data/market_data_<date>.json` 을 읽고, 아래 스키마에 맞춰
   `data/narrative_<date>.json` 을 직접 작성한다. (섹션별 문구, 리스크, 이벤트, 체크포인트 등)

3. **렌더링 + 발송**: `python3 -m scripts.send_infographic --narrative data/narrative_<date>.json`
   HTML 카드 레이아웃을 Playwright(헤드리스 Chromium)로 PNG 인포그래픽으로 캡처한 뒤,
   Gmail SMTP(앱 비밀번호)로 인라인 이미지 이메일을 발송한다. `--dry-run` 으로 발송 없이 PNG만 생성 가능.

## 설치

```bash
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
cp config/secrets.env.example config/secrets.env  # 값 채우기
```

## narrative JSON 스키마

```jsonc
{
  "date": "2026-07-16",
  "title": "7/16 아침 증시 한눈에 보기",
  "subtitle": "미국 반도체 강세 · 금리 안정 · 국내 반도체 반등 기대",
  "quote": {"text": "...", "source": "에이전트 해석"},       // 선택
  "summary": "오늘 시장을 한 줄로 요약",
  "us_market": {"analysis": "미국장이 국내장에 주는 영향 해석"},
  "domestic_mood": {"analysis": "국내 증시 출발 분위기 해석"},
  "sector_highlight": {                                        // 선택
    "title": "반도체 업종 핵심 포인트",
    "bullets": ["메모리 공급 부족 지속 전망"],
    "analysis": "..."
  },
  "events": [{"date": "7/16", "name": "ASML 실적", "note": "..."}],
  "risks": [{"title": "IBM 주가 -25%", "detail": "..."}],
  "checkpoints": ["삼성전자와 SK하이닉스가 시장을 주도하는지"],
  "disclaimer": "..."                                          // 선택, 기본 문구 있음
}
```

`market_data_<date>.json` 의 `indices`(KOSPI/KOSDAQ), `us_indices`(다우/S&P500/나스닥/필라델피아반도체),
`watchlist`(마이크론/IBM/ASML/TSMC 등), `fx_rates`, `rates`, `oil_prices` 는 자동으로 카드에 표/배지로 반영된다.
관심 종목은 `WATCHLIST_TICKERS` 환경변수(`TICKER:라벨,TICKER:라벨` 형식)로 커스터마이즈 가능.

## 클라우드 예약 에이전트(/schedule) 설정

매일 07:30 (Asia/Seoul)에 아래 순서로 실행하는 프롬프트로 등록한다:

1. `python3 -m scripts.collect_data` 실행
2. 생성된 `data/market_data_<date>.json` 을 읽고 위 스키마대로 `data/narrative_<date>.json` 작성
3. `python3 -m scripts.send_infographic --narrative data/narrative_<date>.json` 실행

시크릿(API 키, Gmail 앱 비밀번호)은 클라우드 실행 환경에 별도로 주입해야 한다 (로컬 `config/secrets.env`는 gitignore 대상).

### 네트워크 허용 도메인 (claude.ai Environment 설정)

이 환경(`env_01SooL2oCM2yYvSMYtzLBhGc`, "Default")은 아웃바운드가 기본 차단되어 있어
Network Access를 "사용자 정의"로 설정하고 아래 도메인을 허용해야 한다:

- `api.stlouisfed.org` (FRED)
- `api.eia.gov` (EIA)
- `oapi.koreaexim.go.kr` (한국수출입은행)
- `query1.finance.yahoo.com`, `query2.finance.yahoo.com` (yfinance — KOSPI/KOSDAQ/미국 지수/관심 종목)

`openapi.koreainvestment.com`(KIS)은 비표준 포트(9443)를 쓰는데, 이 프록시는 포트 지정을
지원하지 않아 도메인을 허용해도 TLS 핸드셰이크 단계에서 계속 막힌다 — 그래서 클라우드
파이프라인은 KIS 대신 yfinance로 KOSPI/KOSDAQ을 받는다 (위 참고).
