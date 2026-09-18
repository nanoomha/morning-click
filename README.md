# 나눔보청기(hearkorea.kr) 검색 순위 추적 크롤러

12개 지역 키워드에 대해 `hearkorea.kr`이 구글/네이버 검색 결과(광고 제외)에서
몇 위에 노출되는지 매일 자동으로 조회하고, Excel로 기록하며, 카카오톡으로
알려주는 도구입니다.

## 동작 방식

- 검색엔진은 **하루는 구글, 하루는 네이버**로 자동 교대됩니다 (날짜 기반 결정,
  별도 설정 불필요). `src/schedule_logic.py` 참고.
- 평일 **09:00**: `main_notify_schedule.py` 하나가 다음을 순서대로 모두 처리합니다.
  1. 오늘이 구글/네이버 중 어떤 날인지 안내 메시지를 카톡으로 전송
  2. 이어서 곧바로 12개 키워드 순위를 조회
  3. `data/rank_history.xlsx`에 결과 누적 저장
  4. 순위 결과를 카톡으로 전송 (메시지 하나당 200자 제한에 맞춰 필요하면
     여러 통으로 자동 분할됨)

  즉 안내와 순위 결과가 **9시에 한 번에** 도착합니다 (크롤링에 걸리는 시간만큼
  두 메시지 사이에 약간의 시차는 있을 수 있음). 이전에는 안내(9시)와 순위 결과
  (10시)를 서로 다른 시각에 따로 보냈지만, 이제 하나로 합쳐졌습니다.
- **Windows Task Scheduler가 `python.exe`로 직접, 완전히 무인으로 실행**합니다.
  전송은 `src/kakao_sender.py`가 카카오 REST API(OAuth refresh_token)로 직접
  처리하므로, Claude나 다른 외부 개입이 실행 시점에 전혀 필요 없습니다.
- Excel 컬럼: `날짜 / 키워드 / 검색엔진 / 순위` (순위가 없으면 "미노출").

추적 키워드: 종로보청기, 강남보청기, 수원보청기, 일산보청기, 인천보청기,
분당보청기, 대전보청기, 광주보청기, 대구보청기, 부산보청기(서면),
부산보청기(사상), 울산보청기

## 설치 (Windows)

권장 설치 경로: `C:\nanoom-crawler` (아래 예시는 이 경로 기준이며, 다른 경로에
설치해도 동일하게 동작합니다 — 스케줄러 스크립트가 자기 위치를 기준으로
상대 경로를 사용하기 때문입니다).

1. 이 저장소를 `C:\nanoom-crawler`에 클론하거나 압축 해제.
2. Python 3.10 이상 설치.
3. `C:\nanoom-crawler`에서 가상환경 생성 및 패키지 설치:
   ```
   cd C:\nanoom-crawler
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. `.env.example`을 복사해 `.env`로 만들고 값을 채웁니다:
   ```
   copy .env.example .env
   ```

## 검색 순위 조회 설정 (권장)

무료 스크래핑 방식은 구글/네이버의 HTML 구조 변경이나 자동 차단(캡차)에 취약할
수 있어, 아래 공식 API 등록을 권장합니다. 설정하지 않아도 스크래핑 방식으로
동작은 합니다.

- **네이버**: https://developers.naver.com/apps/#/register 에서 애플리케이션
  등록 후 발급받은 Client ID/Secret을 `.env`의 `NAVER_CLIENT_ID`,
  `NAVER_CLIENT_SECRET`에 입력. (검색 API 사용 설정 필요)
- **구글**: https://serpapi.com 가입 후 API Key를 `.env`의 `SERPAPI_KEY`에 입력.
  (무료 플랜 월 100회 제공)
  - 설정하지 않으면 Selenium(헤드리스 Chrome)으로 google.com을 직접 렌더링해
    순위를 조회합니다. 이 경우 **PC에 Google Chrome이 설치되어 있어야** 합니다
    (Selenium 4.6+ 는 chromedriver를 자동으로 관리하므로 별도 설치는 불필요).

## 카카오톡 알림 설정 (필수)

1. https://developers.kakao.com 에서 애플리케이션 생성.
2. [제품 설정 > 카카오 로그인] 활성화, Redirect URI에 `.env`의
   `KAKAO_REDIRECT_URI` 값과 동일하게 등록. (실제로 접속 가능한 서버일 필요는
   없습니다. 로그인 후 리디렉션되는 주소창의 URL만 복사하면 됩니다.)
3. [카카오 로그인 > 동의항목]에서 "카카오톡 메시지 전송"(`talk_message`) 항목을
   사용 설정으로 변경.
4. [앱 키]의 REST API 키를 `.env`의 `KAKAO_REST_API_KEY`에 입력.
5. [카카오 로그인 > 보안]에서 Client Secret이 "사용함(필수)"으로 설정되어
   있다면, 그 값을 `.env`의 `KAKAO_CLIENT_SECRET`에 입력 (그 외에는 비워둠).
   이걸 빠뜨리면 인증 시 `401` 에러가 발생합니다.
6. 최초 1회 아래 명령 실행 후 안내에 따라 브라우저 로그인/동의를 완료합니다:
   ```
   python kakao_auth_setup.py
   ```
   완료되면 `data/kakao_token.json`에 토큰이 저장되고, 이후 자동으로 토큰이
   갱신되며 별도 재인증이 필요 없습니다 (카카오 refresh_token 만료 정책상,
   장기간 미실행 시에는 재인증이 필요할 수 있습니다).

## 수동 실행 (테스트)

```
python main_notify_schedule.py   # 9시 작업 전체 테스트: 안내 → 크롤링 → 결과, 모두 카톡 전송
python main_crawl.py             # (선택) 순위 조회만 다시 돌려보고 싶을 때 단독 실행
```

## Windows Task Scheduler 자동 등록

관리자 권한 PowerShell에서 (예: `C:\nanoom-crawler\scheduler`):

```
cd C:\nanoom-crawler\scheduler
powershell -ExecutionPolicy Bypass -File .\setup_task_scheduler.ps1
```

`setup_task_scheduler.ps1`은 자기 위치(`$PSScriptRoot`)를 기준으로 상대 경로를
사용하므로, 저장소를 다른 경로에 설치했어도 그대로 동작합니다. 다음 작업이
평일 기준으로 등록됩니다 (이전 버전에서 등록했던 10:00 `HearKorea_Rank_Crawl`
작업이 남아있다면 자동으로 제거됩니다):

| 작업 이름 | 시간 | 내용 |
|---|---|---|
| HearKorea_Schedule_Notify | 09:00 | `python main_notify_schedule.py` 실행 → 스케줄 안내 + 순위 조회 + 엑셀 저장 + 결과, 모두 카톡 전송 |

`taskschd.msc`(작업 스케줄러)에서 등록 상태를 확인/수정할 수 있습니다. 실행
로그는 `C:\nanoom-crawler\logs\notify.log`에 쌓이므로, 등록 후 로그를 보고
실제 실행/전송이 잘 되는지 확인하세요.

### 참고: Play MCP MemoChat을 통한 수동/테스트 전송

Claude Code 세션에서 대화 중에 `python main_notify_schedule.py`나
`main_crawl.py`의 출력을 즉석에서 카톡으로 보내보고 싶다면, Play MCP의
`KakaotalkChat-MemoChat` 도구(파라미터: `message` 문자열, 최대 200자)를
Claude가 직접 호출할 수도 있습니다. 다만 이 도구는 **Claude 에이전트 세션
안에서만 호출 가능**하고, 이 세션은 최대 7일 후 자동 만료되는 인메모리
작업이라 "매일 자동 실행"의 정식 경로로는 쓸 수 없습니다 — 위 Windows Task
Scheduler + `kakao_sender.py`(OAuth 직접 호출) 방식이 실제 운영용 경로입니다.

## 폴더 구조

```
C:\nanoom-crawler\
  config.py                   # 키워드/도메인/경로 등 전역 설정
  main_notify_schedule.py     # 9시 자동 실행 진입점: 스케줄 안내 → 크롤링 → 결과 전송
  main_crawl.py                # 순위 조회/엑셀 저장/메시지 분할 로직 (위 스크립트가 불러다 씀,
                                #   필요시 수동 단독 실행도 가능)
  kakao_auth_setup.py          # 카카오 최초 인증(1회, 대화형)
  src/
    schedule_logic.py          # 구글/네이버 교대 로직
    excel_writer.py            # 엑셀 누적 저장
    kakao_sender.py            # 카카오 "나에게 보내기" 전송 (OAuth REST API)
    search/
      google_search.py         # 구글 순위 조회 (SerpApi 또는 Selenium 스크래핑)
      naver_search.py          # 네이버 순위 조회 (오픈API 또는 스크래핑)
  scheduler/
    setup_task_scheduler.ps1   # 작업 스케줄러 등록 스크립트 (09:00 작업 1개)
    run_notify.bat              # Task Scheduler가 실행 (main_notify_schedule.py)
    run_crawl.bat                # 수동 재실행용 (main_crawl.py 단독 실행)
  data/
    rank_history.xlsx          # 결과 누적 저장 (자동 생성)
    kakao_token.json           # 카카오 토큰 (자동 생성, git에 포함 안 됨)
  logs/
    notify.log                 # Task Scheduler 실행 로그 (자동 생성)
```

## 참고 및 한계

- 무료 스크래핑 방식(구글/네이버 API 미설정 시)은 검색엔진의 HTML 구조 변경이나
  IP 차단/캡차에 영향을 받을 수 있습니다. 실패 시 로그에 원인이 출력되며, 해당
  키워드는 "미노출"로 기록되고 나머지 키워드 조회는 계속 진행됩니다.
- 카카오 메시지는 하나당 최대 200자로 보냅니다. `main_crawl.py`는 이 한도를
  넘지 않도록 결과를 자동으로 여러 통으로 나눠 순서대로 전송합니다
  (`build_summary_chunks` 참고).
- 카카오 "나에게 보내기"는 비즈니스 채널 심사 없이 개인 알림 용도로 사용할 수
  있는 방식입니다. 여러 명에게 보내려면 별도의 카카오톡 채널/알림톡 연동이
  필요합니다.
- 카카오 refresh_token은 장기간(수개월) 미실행 시 만료되어 재인증
  (`python kakao_auth_setup.py`)이 필요할 수 있습니다.
