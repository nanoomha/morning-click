# 나눔보청기(hearkorea.kr) 검색 순위 추적 크롤러

12개 지역 키워드에 대해 `hearkorea.kr`이 구글/네이버 검색 결과(광고 제외)에서
몇 위에 노출되는지 매일 자동으로 조회하고, Excel로 기록하며, 카카오톡("나에게
보내기")으로 알려주는 도구입니다.

## 동작 방식

- 검색엔진은 **하루는 구글, 하루는 네이버**로 자동 교대됩니다 (날짜 기반 결정,
  별도 설정 불필요). `src/schedule_logic.py` 참고.
- 평일 **09:00**: 오늘이 구글/네이버 중 어떤 날인지 카톡으로 안내.
- 평일 **10:00**: 12개 키워드 순위를 조회 → `data/rank_history.xlsx`에 누적 저장
  → 결과를 카톡으로 전송.
- Excel 컬럼: `날짜 / 키워드 / 검색엔진 / 순위` (순위가 없으면 "미노출").

추적 키워드: 종로보청기, 강남보청기, 수원보청기, 일산보청기, 인천보청기,
분당보청기, 대전보청기, 광주보청기, 대구보청기, 부산보청기(서면),
부산보청기(사상), 울산보청기

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

## 카카오톡 알림 설정 (필수)

1. https://developers.kakao.com 에서 애플리케이션 생성.
2. [제품 설정 > 카카오 로그인] 활성화, Redirect URI에 `.env`의
   `KAKAO_REDIRECT_URI` 값(기본 `https://localhost.com/oauth`)과 동일하게 등록.
   (실제로 접속 가능한 서버일 필요는 없습니다. 로그인 후 리디렉션되는 주소창의
   URL만 복사하면 됩니다.)
3. [카카오 로그인 > 동의항목]에서 "카카오톡 메시지 전송"(`talk_message`) 항목을
   사용 설정으로 변경.
4. [앱 키]의 REST API 키를 `.env`의 `KAKAO_REST_API_KEY`에 입력.
5. 최초 1회 아래 명령 실행 후 안내에 따라 브라우저 로그인/동의를 완료합니다:
   ```
   python kakao_auth_setup.py
   ```
   완료되면 `data/kakao_token.json`에 토큰이 저장되고, 이후 자동으로 토큰이
   갱신되며 별도 재인증이 필요 없습니다 (카카오 refresh_token 만료 정책상,
   장기간 미실행 시에는 재인증이 필요할 수 있습니다).

## 수동 실행 (테스트)

```
python main_notify_schedule.py   # 9시 알림 테스트
python main_crawl.py             # 10시 크롤링 + 엑셀 저장 + 결과 알림 테스트
```

## Windows Task Scheduler 자동 등록

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
로그는 `logs\notify.log`, `logs\crawl.log`에 쌓입니다.

## 폴더 구조

```
config.py                     # 키워드/도메인/경로 등 전역 설정
main_notify_schedule.py       # 9시 알림 진입점
main_crawl.py                 # 10시 크롤링 진입점
kakao_auth_setup.py           # 카카오 최초 인증(1회)
src/
  schedule_logic.py           # 구글/네이버 교대 로직
  excel_writer.py             # 엑셀 누적 저장
  kakao_sender.py             # 카카오 "나에게 보내기" 전송
  search/
    google_search.py          # 구글 순위 조회 (SerpApi 또는 스크래핑)
    naver_search.py           # 네이버 순위 조회 (오픈API 또는 스크래핑)
scheduler/
  setup_task_scheduler.ps1    # 작업 스케줄러 등록 스크립트
  run_notify.bat / run_crawl.bat
data/
  rank_history.xlsx           # 결과 누적 저장 (자동 생성)
  kakao_token.json            # 카카오 토큰 (자동 생성, git에 포함 안 됨)
```

## 참고 및 한계

- 무료 스크래핑 방식(구글/네이버 API 미설정 시)은 검색엔진의 HTML 구조 변경이나
  IP 차단/캡차에 영향을 받을 수 있습니다. 실패 시 로그에 원인이 출력되며, 해당
  키워드는 "미노출"로 기록되고 나머지 키워드 조회는 계속 진행됩니다.
- 카카오 "나에게 보내기"는 비즈니스 채널 심사 없이 개인 알림 용도로 사용할 수
  있는 방식입니다. 여러 명에게 보내려면 별도의 카카오톡 채널/알림톡 연동이
  필요합니다.
