# 나눔보청기(hearkorea.kr) 검색 순위 추적 크롤러

나눔보청기 12개 지점에 대해, 구글에서는 `hearkorea.kr` 홈페이지의 (광고 제외)
검색 순위를, 네이버에서는 네이버 플레이스(지도) 순위를 매 영업일 자동으로
조회하고, Excel로 기록하며, 카카오톡으로 알려주는 도구입니다.

## 동작 방식

12개 지점을 3개씩 A/B/C/D 4개 그룹으로 나누고, **영업일(평일이면서 대한민국
공휴일·대체공휴일이 아닌 날) 하루에 한 그룹씩**, "구글 하루 → 네이버 하루"
순서로 8단계를 계속 순환합니다:

```
A그룹 구글 → A그룹 네이버 → B그룹 구글 → B그룹 네이버
→ C그룹 구글 → C그룹 네이버 → D그룹 구글 → D그룹 네이버 → (다시 A그룹 구글)
```

주말/공휴일은 건너뛰고, 순환 순서에는 영향을 주지 않습니다 (건너뛴 날짜는
그냥 세지 않을 뿐). 이 순환은 2026-09-18(A그룹 구글이었던 날)을 기준으로
계산되어, 별도 상태 파일 없이도 날짜만으로 항상 같은 결과가 나옵니다
(`src/schedule_logic.py`).

| 그룹 | 지점 |
|---|---|
| A | 일산, 인천부천, 분당 |
| B | 대전, 광주, 대구 |
| C | 부산서면, 부산사상, 울산 |
| D | 종로, 강남, 수원 |

지점별 검색어/조회 대상은 `config.py`의 `LOCATIONS`에 정의되어 있습니다.
대부분 지점은 구글/네이버 검색어가 같지만, **인천부천점만 예외**로 구글은
"인천보청기", 네이버는 "부천보청기"로 검색합니다.

- **구글 날**: 각 지점의 검색어로 hearkorea.kr 홈페이지가 (광고 제외) 몇
  번째에 나오는지 조회.
- **네이버 날**: 각 지점의 검색어로 **네이버 플레이스(지도)**를 검색해, 그
  지점의 등록 업체명이 몇 번째에 나오는지 조회 (홈페이지 웹검색 순위가 아님).
  같은 검색어를 쓰는 지점(부산서면/부산사상 둘 다 "부산보청기")은 검색을
  한 번만 하고 결과를 나눠 씁니다.

평일 **09:00**: `main_notify_schedule.py` 하나가 다음을 순서대로 모두
처리합니다.
1. 오늘이 영업일이 아니면(주말/공휴일) 아무것도 하지 않고 조용히 종료
2. 영업일이면, 오늘이 어느 그룹·어느 엔진 차례인지 안내를 카톡으로 전송
3. 이어서 곧바로 그 그룹 3개 지점의 순위 조회
4. `data/rank_history.xlsx`에 결과 누적 저장 (컬럼: 날짜/그룹/지점/검색엔진/검색어/순위)
5. 순위 결과를 카톡으로 전송 (메시지 하나당 200자 제한에 맞춰 필요하면
   여러 통으로 자동 분할됨)

**Windows Task Scheduler가 `python.exe`로 직접, 완전히 무인으로 실행**합니다
(Task Scheduler 자체는 공휴일을 모르므로, 공휴일 스킵은 위 1번처럼 스크립트가
직접 판단합니다). 전송은 `src/kakao_sender.py`가 카카오 REST API(OAuth
refresh_token)로 직접 처리하므로, Claude나 다른 외부 개입이 실행 시점에
전혀 필요 없습니다.

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

## 검색 순위 조회 설정

- **구글**: https://serpapi.com 가입 후 API Key를 `.env`의 `SERPAPI_KEY`에
  입력하면 SerpApi로 조회합니다 (무료 플랜 월 100회 제공, 권장 — 이 스케줄은
  구글 조회가 한 달에 30회 안팎이라 무료 플랜으로 충분함). 실제 고객 대부분이
  모바일로 검색하므로 **모바일 검색 결과 기준**으로 조회합니다(PC 검색과
  순위가 다를 수 있음). 설정하지 않으면 Selenium(헤드리스 Chrome, 마찬가지로
  모바일 화면으로 렌더링)으로 google.com을 직접 스크래핑합니다 — 이 경우
  **PC에 Google Chrome이 설치되어 있어야** 하고, 크롬이 자동화된 실행을
  차단당하거나(백신 등) 버전이 안 맞으면 실패할 수 있어 SerpApi 쪽이 더
  안정적입니다.
- **네이버 플레이스**: 별도 API 키가 필요 없습니다. 네이버 지도가 내부적으로
  쓰는 검색 API를 그대로 호출합니다 (`src/search/naver_place_search.py`).
  다만 이건 네이버 공식 API가 아니라서, 네이버가 응답 구조를 바꾸면 깨질 수
  있습니다 — 처음 실행했을 때 결과가 이상하면(전부 미노출 등) 로그의 에러
  메시지를 확인해 알려주세요.

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
python main_notify_schedule.py   # 오늘 실제 자동 실행과 동일하게 전체 테스트
python main_crawl.py             # (선택) 순위 조회만 다시 돌려보고 싶을 때 단독 실행
```
오늘이 주말/공휴일이면 두 스크립트 모두 "오늘은 실행하지 않습니다"라고만 출력하고
아무 것도 전송하지 않습니다 — 테스트하려면 영업일에 실행하세요.

## Windows Task Scheduler 자동 등록

관리자 권한 PowerShell에서 (예: `C:\nanoom-crawler\scheduler`):

```
cd C:\nanoom-crawler\scheduler
powershell -ExecutionPolicy Bypass -File .\setup_task_scheduler.ps1
```

`setup_task_scheduler.ps1`은 자기 위치(`$PSScriptRoot`)를 기준으로 상대 경로를
사용하므로, 저장소를 다른 경로에 설치했어도 그대로 동작합니다. 다음 작업이
평일 기준으로 등록됩니다 (공휴일 자체는 스크립트가 판단합니다):

| 작업 이름 | 시간 | 내용 |
|---|---|---|
| HearKorea_Schedule_Notify | 09:00 | `python main_notify_schedule.py` 실행 → (영업일이면) 스케줄 안내 + 순위 조회 + 엑셀 저장 + 결과, 모두 카톡 전송 |

`taskschd.msc`(작업 스케줄러)에서 등록 상태를 확인/수정할 수 있습니다. 실행
로그는 `C:\nanoom-crawler\logs\notify.log`에 쌓이므로, 등록 후 로그를 보고
실제 실행/전송이 잘 되는지 확인하세요.

## 폴더 구조

```
C:\nanoom-crawler\
  config.py                   # 지점 목록(LOCATIONS)/그룹/순환 기준일 등 전역 설정
  main_notify_schedule.py     # 9시 자동 실행 진입점: 스케줄 안내 → 크롤링 → 결과 전송
  main_crawl.py                # 그룹별 순위 조회/엑셀 저장/메시지 분할 로직 (위 스크립트가
                                #   불러다 씀, 필요시 수동 단독 실행도 가능)
  kakao_auth_setup.py          # 카카오 최초 인증(1회, 대화형)
  src/
    schedule_logic.py          # 영업일 판정 + A~D 그룹/구글·네이버 순환 로직
    excel_writer.py            # 엑셀 누적 저장
    kakao_sender.py            # 카카오 "나에게 보내기" 전송 (OAuth REST API)
    search/
      google_search.py         # 구글 홈페이지 순위 조회 (SerpApi 또는 Selenium 스크래핑)
      naver_place_search.py    # 네이버 플레이스(지도) 순위 조회 (비공식 API)
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

- **네이버 플레이스 조회는 비공식 API를 씁니다.** 네이버가 응답 구조를
  바꾸면 예고 없이 깨질 수 있습니다. 특정 지점이 계속 "미노출"로만 나오는데
  실제로는 노출되고 있어야 한다면, 이 API 응답 구조가 바뀐 것일 수 있으니
  로그를 보고 알려주세요 (`src/search/naver_place_search.py`의
  `_extract_place_names()`를 실제 응답에 맞게 고치면 됩니다).
- 네이버 플레이스 업체명은 **부분 문자열 일치**로 찾습니다 (`config.py`의
  `naver_place_name`이 실제 검색 결과 업체명에 포함되는지). 비슷한 이름의
  다른 지점/업체가 있으면 잘못 매칭될 수 있으니 상호명을 정확히 입력하세요.
- 무료 구글 스크래핑 방식(SerpApi 미설정 시)은 구글의 HTML 구조 변경이나
  IP 차단/캡차에 영향을 받을 수 있습니다. 실패 시 로그에 원인이 출력되며,
  해당 지점은 "미노출"로 기록되고 나머지 지점 조회는 계속 진행됩니다.
- 대한민국 공휴일 판정은 `holidays` 파이썬 패키지를 사용합니다(설날/추석
  등 음력 공휴일과 대체공휴일 포함, 매년 자동 계산). 지방선거일처럼 그해에만
  임시로 지정되는 공휴일도 이 패키지가 최신 정보를 반영하고 있다면 함께
  스킵됩니다.
- 카카오 메시지는 하나당 최대 200자로 보냅니다. 결과가 길어지면 자동으로
  여러 통으로 나눠 순서대로 전송합니다 (`build_summary_chunks` 참고).
- 카카오 "나에게 보내기"는 비즈니스 채널 심사 없이 개인 알림 용도로 사용할 수
  있는 방식입니다. 여러 명에게 보내려면 별도의 카카오톡 채널/알림톡 연동이
  필요합니다.
- 카카오 refresh_token은 장기간(수개월) 미실행 시 만료되어 재인증
  (`python kakao_auth_setup.py`)이 필요할 수 있습니다.
