# kr-market-report

매일 아침 국내/국외 증시 지표를 수집해 카드형 인포그래픽 이미지를 만들고 이메일로 발송하는 파이프라인.

## 파이프라인 (2단계)

이 리포트는 스크립트가 수치를 "해석"하지 않는다 — 해석(서술)은 매일 이 파이프라인을 실행하는
**클라우드 예약 Claude 에이전트**가 수집된 수치를 보고 직접 작성한다. 그래서 별도 LLM API 키가 필요 없다.

1. **데이터 수집**: `python3 -m scripts.collect_data [--date YYYY-MM-DD]`
   FRED(미국 금리) / EIA(유가) / 한국수출입은행(환율) / 네이버 금융(KOSPI·KOSDAQ) / Twelve Data(미국
   지수) / Finnhub(관심 종목)를 조회해 `data/market_data_<date>.json` 으로 저장한다.

   데이터 소스는 여러 번의 클라우드 실행 환경 제약 때문에 아래처럼 바뀌었다:
   - **KOSPI/KOSDAQ**: KIS Open API(`kis_client.py`, 비표준 포트 9443이 프록시에 막힘) →
     yfinance(`curl_cffi`의 TLS 위장이 프록시와 충돌 + 레이트리밋으로 불안정) → 현재는
     **네이버 금융 공개 API**(`naver_client.py`, 키 불필요, 표준 HTTPS, 최근 15거래일 종가 추이도
     함께 받는다). 비공식 API라 필드가 바뀔 수 있음에 유의.
   - **미국 지수(다우/S&P500/나스닥/필라델피아반도체)**: yfinance → **Twelve Data**(`twelvedata_client.py`).
     무료 티어는 실제 지수 심볼(`DJI`, `IXIC` 등) 접근이 막혀있어, 해당 지수를 추종하는
     ETF(`DIA`/`SPY`/`ONEQ`/`SOXX`)의 등락률과 15거래일 종가 추이를 대리 지표로 쓴다.
   - **관심 종목(반도체 관련주 등)**: yfinance → **Finnhub**(`finnhub_client.py`, 현재가/등락률과
     앞으로 30일 내 실적 발표 일정). Finnhub 무료 티어는 과거 시세(캔들)를 안 줘서, 종목별 추이는
     Twelve Data에서 별도로 받아 합친다(`collect_data.py`의 `_attach_watchlist_history`).

   `kis_client.py`/`yfinance_client.py`는 해당 소스 접속이 가능한 환경(로컬 등)에서 대안으로 쓸 수
   있도록 레포에 남겨뒀지만 기본 파이프라인에서는 쓰지 않는다.

2. **해석 작성**: 에이전트가 `data/market_data_<date>.json` 을 읽고, 아래 스키마에 맞춰
   `data/narrative_<date>.json` 을 직접 작성한다. (섹션별 문구, 리스크, 이벤트, 체크포인트 등)

3. **렌더링 + 발송**: `python3 -m scripts.send_infographic --narrative data/narrative_<date>.json`
   HTML 카드 레이아웃을 Playwright(헤드리스 Chromium)로 PNG 인포그래픽으로 캡처한 뒤,
   Resend API(HTTPS)로 이미지를 본문에 내장한 이메일을 발송한다. `--dry-run` 으로 발송 없이 PNG만 생성 가능.

   원래는 Gmail SMTP(587, 앱 비밀번호)를 썼지만, 클라우드 예약 에이전트 샌드박스의 아웃바운드
   프록시가 HTTPS(443) 외의 프로토콜/포트를 지원하지 않아 SMTP 자체가 불가능해 Resend(순수
   HTTPS REST API)로 교체했다.

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

`market_data_<date>.json` 의 `indices`(KOSPI/KOSDAQ), `us_indices`(다우/S&P500/나스닥/필라델피아반도체
ETF 대리 지표), `watchlist`(마이크론/IBM/ASML/TSMC 등)에는 각각 `history`(최근 15거래일 종가, 과거→최신
순) 배열이 들어있고, 인포그래픽이 이걸로 배지 아래에 스파크라인을 자동으로 그린다 — narrative에서 굳이
"최근 추이" 문구를 따로 언급하지 않아도 그림으로 보인다. `earnings_calendar`(향후 30일 내 워치리스트
종목의 실적 발표 예정일, Finnhub)도 있는데, `events` 섹션을 채울 때 여기 있는 실제 날짜를 우선 활용하고
없는데 지어내지는 말 것. `fx_rates`, `rates`, `oil_prices` 는 자동으로 카드에 표로 반영된다. 관심 종목은
`WATCHLIST_TICKERS` 환경변수(`TICKER:라벨,TICKER:라벨` 형식, Finnhub가 지원하는 미국 상장 종목 티커)로
커스터마이즈 가능.

## 클라우드 예약 에이전트(/schedule) 설정

매일 07:30 (Asia/Seoul)에 아래 순서로 실행하는 프롬프트로 등록한다:

1. `python3 -m scripts.collect_data` 실행
2. 생성된 `data/market_data_<date>.json` 을 읽고 위 스키마대로 `data/narrative_<date>.json` 작성
3. `python3 -m scripts.send_infographic --narrative data/narrative_<date>.json` 실행

시크릿(API 키, Resend API 키)은 클라우드 실행 환경에 별도로 주입해야 한다 (로컬 `config/secrets.env`는 gitignore 대상).

### 네트워크 허용 도메인 (claude.ai Environment 설정)

이 환경(`env_01SooL2oCM2yYvSMYtzLBhGc`, "Default")은 아웃바운드가 기본 차단되어 있어
Network Access를 "사용자 정의"로 설정하고 아래 도메인을 허용해야 한다:

- `api.stlouisfed.org` (FRED)
- `api.eia.gov` (EIA)
- `oapi.koreaexim.go.kr` (한국수출입은행)
- `m.stock.naver.com` (네이버 금융 — KOSPI/KOSDAQ 현재가+추이)
- `api.twelvedata.com` (미국 지수 ETF 대리 지표)
- `finnhub.io` (관심 종목)
- `api.resend.com` (이메일 발송)

이 프록시는 HTTPS(443)만 지원한다 — 그래서 겪었던 두 가지 구조적 제약:

- `openapi.koreainvestment.com`(KIS)은 비표준 포트(9443)를 써서 도메인을 허용해도 TLS
  핸드셰이크 단계에서 막힌다.
- Gmail SMTP(587)도 같은 이유로 원천적으로 불가능해 Resend(HTTPS)로 교체했다.

yfinance는 `curl_cffi`로 브라우저 TLS 지문을 흉내내 Yahoo의 봇 차단을 우회하는데, 이 위장 TLS
핸드셰이크가 이 프록시 터널과 충돌해 접속이 끊기거나(도메인 허용과 무관), 레이트리밋(429)에
걸리는 경우가 잦아 결국 Naver/Twelve Data/Finnhub 조합으로 교체했다.

`scripts/collect_data.py`는 각 소스별 수집 실패를 best-effort로 흡수한다 — 예를 들어 네이버가
일시적으로 응답하지 않아도 나머지 소스(FX/금리/유가/미국 지수/관심 종목)만으로 리포트가 발송된다.
