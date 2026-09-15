# 나눔보청기(hearkorea.kr) 검색 순위 추적 크롤러

12개 지역 키워드에 대해 `hearkorea.kr`이 구글/네이버 검색 결과(광고 제외)에서
몇 위에 노출되는지 매일 자동으로 조회하고, Excel로 기록하며, 카카오톡으로
알려주는 도구입니다.

## 동작 방식

- 검색엔진은 **하루는 구글, 하루는 네이버**로 자동 교대됩니다 (날짜 기반 결정,
  별도 설정 불필요). `src/schedule_logic.py` 참고.
- 평일 **09:00**: `main_notify_schedule.py`가 오늘이 구글/네이버 중 어떤 날인지
  안내 메시지를 계산해 표준출력(stdout)으로 출력.
- 평일 **10:00**: `main_crawl.py`가 12개 키워드 순위를 조회 → `data/rank_history.xlsx`에
  누적 저장 → 결과 메시지를 표준출력으로 출력 (200자 제한에 맞춰 자동으로 여러
  메시지로 분할됨).
- Excel 컬럼: `날짜 / 키워드 / 검색엔진 / 순위` (순위가 없으면 "미노출").

추적 키워드: 종로보청기, 강남보청기, 수원보청기, 일산보청기, 인천보청기,
분당보청기, 대전보청기, 광주보청기, 대구보청기, 부산보청기(서면),
부산보청기(사상), 울산보청기

## 카카오톡 전송 방식 (중요)

두 스크립트는 **더 이상 카카오톡을 직접 전송하지 않습니다.** 대신 메시지 내용을
표준출력에만 깔끔하게 출력합니다. 실제 전송은 Play MCP의
`KakaotalkChat-MemoChat` MCP 도구(파라미터: `message` 문자열, 최대 200자)를
호출해서 이루어지며, 이 도구는 **Claude 에이전트 세션 안에서만 호출 가능**하고
일반 `python.exe` 프로세스에서는 호출할 수 없습니다.

즉 전체 흐름은:
```
(Claude 세션) python main_notify_schedule.py 실행
            → stdout으로 메시지 읽기
            → mcp: KakaotalkChat-MemoChat(message=...) 호출 → 카톡 전송

(Claude 세션) python main_crawl.py 실행
            → stdout을 "\n<<<MEMOCHAT_SPLIT>>>\n" 기준으로 분리
            → 각 조각마다 MemoChat(message=...) 호출 → 카톡 전송(여러 통일 수 있음)
```

**⚠️ 자동화 한계**: 이 흐름이 "매일 평일 9시/10시에" 실행되려면 그 시각에
Claude 에이전트 세션이 살아있으면서 스케줄을 트리거해야 합니다. 이 저장소
자체에는 그런 상시 실행 주체가 없습니다 — 다음 중 하나가 필요합니다.

1. **Claude Code의 Cron 기능으로 트리거** — 다만 이 방식은 세션 안에서만
   유지되는 인메모리 작업이라 세션이 끝나거나(비활성 시 컨테이너 회수 등)
   최대 7일이 지나면 자동 만료되어 재등록해야 합니다. "몇 달간 무인 자동화"
   용도로는 부적합하고, 짧은 기간 테스트/데모에 적합합니다.
2. **Windows Task Scheduler + 카카오 REST API 직접 호출** — MemoChat 없이,
   `src/kakao_sender.py`(카카오 "나에게 보내기" OAuth 방식)를 다시 연결해
   완전히 독립적으로 몇 년이고 무인 실행되게 하는 기존 방식. 아래
   [대안: MemoChat 없이 완전 자동화](#대안-memochat-없이-완전-자동화) 참고.

어느 쪽을 쓸지는 실제 운영 요구사항(무인 기간)에 따라 정해야 합니다.

## 설치 (Windows)

1. Python 3.10 이상 설치.
2. 프로젝트 폴더에서 가상환경 생성 및 패키지 설치:
   ```
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. `.env.example`을 복사해 `.env`로 만들고 값을 채웁니다:
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

## 수동 실행 (테스트)

```
python main_notify_schedule.py   # 9시 안내 메시지를 stdout에 출력
python main_crawl.py             # 10시 크롤링 + 엑셀 저장 + 결과 메시지를 stdout에 출력
```
출력된 내용을 Claude 세션에서 읽어 `KakaotalkChat-MemoChat(message=...)`으로
전달하면 카카오톡 "나와의 채팅"으로 전송됩니다. `main_crawl.py`의 출력은
`<<<MEMOCHAT_SPLIT>>>` 구분자로 나뉜 여러 메시지일 수 있으니, 그 구분자로
나눠 각각 MemoChat을 호출해야 합니다.

## 대안: MemoChat 없이 완전 자동화

Claude 세션 없이 Windows PC에서 몇 달~몇 년이고 무인으로 자동 실행하고
싶다면, MemoChat 대신 카카오 "나에게 보내기" REST API를 직접 호출하는
기존 방식을 쓸 수 있습니다. 이 저장소에는 그 코드(`src/kakao_sender.py`,
`kakao_auth_setup.py`)가 남아 있으나, 현재 `main_notify_schedule.py`/
`main_crawl.py`는 이를 호출하지 않도록 분리되어 있습니다.

1. https://developers.kakao.com 에서 애플리케이션 생성.
2. [제품 설정 > 카카오 로그인] 활성화, Redirect URI에 `.env`의
   `KAKAO_REDIRECT_URI` 값과 동일하게 등록.
3. [카카오 로그인 > 동의항목]에서 "카카오톡 메시지 전송"(`talk_message`) 항목을
   사용 설정으로 변경.
4. [앱 키]의 REST API 키를 `.env`의 `KAKAO_REST_API_KEY`에 입력.
5. 최초 1회 `python kakao_auth_setup.py` 실행 후 브라우저 로그인/동의를 완료.
6. `main_notify_schedule.py`/`main_crawl.py`에 `from src.kakao_sender import
   send_text_to_me`를 다시 추가하고, 메시지를 출력하기 전에 `send_text_to_me(message)`를
   호출하도록 되돌립니다.
7. 아래 Windows Task Scheduler 등록을 진행합니다.

### Windows Task Scheduler 등록

관리자 권한 PowerShell에서:

```
cd scheduler
powershell -ExecutionPolicy Bypass -File .\setup_task_scheduler.ps1
```

다음 두 작업이 평일 기준으로 등록됩니다:

| 작업 이름 | 시간 | 내용 |
|---|---|---|
| HearKorea_Schedule_Notify | 09:00 | 오늘의 스케줄 안내 |
| HearKorea_Rank_Crawl | 10:00 | 순위 조회 + 엑셀 저장 + 결과 알림 |

`taskschd.msc`(작업 스케줄러)에서 등록 상태를 확인/수정할 수 있습니다. 실행
로그는 `logs\notify.log`, `logs\crawl.log`에 쌓입니다. (6번을 되돌리지 않으면
이 로그에는 메시지가 출력되기만 하고 실제 카톡 전송은 되지 않습니다.)

## 폴더 구조

```
config.py                     # 키워드/도메인/경로 등 전역 설정
main_notify_schedule.py       # 9시 안내 메시지 계산 → stdout 출력
main_crawl.py                 # 10시 크롤링 + 엑셀 저장 → 결과 메시지 stdout 출력
kakao_auth_setup.py           # [대안 경로용] 카카오 최초 인증(1회)
src/
  schedule_logic.py           # 구글/네이버 교대 로직
  excel_writer.py             # 엑셀 누적 저장
  kakao_sender.py             # [대안 경로용] 카카오 "나에게 보내기" 전송
  search/
    google_search.py          # 구글 순위 조회 (SerpApi 또는 스크래핑)
    naver_search.py           # 네이버 순위 조회 (오픈API 또는 스크래핑)
scheduler/
  setup_task_scheduler.ps1    # [대안 경로용] 작업 스케줄러 등록 스크립트
  run_notify.bat / run_crawl.bat
data/
  rank_history.xlsx           # 결과 누적 저장 (자동 생성)
  kakao_token.json            # [대안 경로용] 카카오 토큰 (자동 생성, git에 포함 안 됨)
```

## 참고 및 한계

- 무료 스크래핑 방식(구글/네이버 API 미설정 시)은 검색엔진의 HTML 구조 변경이나
  IP 차단/캡차에 영향을 받을 수 있습니다. 실패 시 로그에 원인이 출력되며, 해당
  키워드는 "미노출"로 기록되고 나머지 키워드 조회는 계속 진행됩니다.
- MemoChat은 메시지당 최대 200자까지만 지원합니다. `main_crawl.py`는 이 한도를
  넘지 않도록 결과를 자동으로 여러 메시지로 나눠 출력합니다
  (`build_summary_chunks` 참고).
- 카카오 "나에게 보내기"(대안 경로)는 비즈니스 채널 심사 없이 개인 알림 용도로
  사용할 수 있는 방식입니다. 여러 명에게 보내려면 별도의 카카오톡 채널/알림톡 연동이
  필요합니다.
