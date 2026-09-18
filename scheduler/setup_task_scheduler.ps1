<#
.SYNOPSIS
    나눔보청기 순위 추적 크롤러를 Windows Task Scheduler에 등록한다.

.DESCRIPTION
    아래 작업을 평일(월~금) 기준으로 등록한다.
      - HearKorea_Schedule_Notify : 매일 09:00, 오늘의 스케줄 안내 + 순위 조회 +
                                    Excel 저장 + 결과까지 한 번에 카톡 전송

    예전에는 09:00 안내와 10:00 순위 조회를 별도 작업 두 개로 나눠 등록했지만,
    이제 main_notify_schedule.py가 스케줄 안내 직후 순위 조회까지 이어서 처리하므로
    09:00 작업 하나만 등록한다. 예전 버전으로 이 스크립트를 이미 실행해 10:00
    작업(HearKorea_Rank_Crawl)이 남아있다면 자동으로 제거한다.

.NOTES
    반드시 "관리자 권한"으로 PowerShell을 실행한 뒤 이 스크립트를 실행하세요.
    예) 이 폴더에서: powershell -ExecutionPolicy Bypass -File .\setup_task_scheduler.ps1
#>

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$NotifyBat = Join-Path $ProjectRoot "scheduler\run_notify.bat"

function Register-DailyWeekdayTask {
    param(
        [string]$TaskName,
        [string]$ScriptPath,
        [string]$Time
    )

    $action = New-ScheduledTaskAction -Execute $ScriptPath -WorkingDirectory $ProjectRoot
    $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At $Time
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd

    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
        -Settings $settings -Description "나눔보청기 순위 추적 크롤러: $TaskName" -Force | Out-Null

    Write-Host "등록 완료: $TaskName ($Time, 평일)"
}

# 예전 버전에서 등록했을 수 있는 10:00 별도 작업 제거 (9:00 작업에 통합됨)
Unregister-ScheduledTask -TaskName "HearKorea_Rank_Crawl" -Confirm:$false -ErrorAction SilentlyContinue

Register-DailyWeekdayTask -TaskName "HearKorea_Schedule_Notify" -ScriptPath $NotifyBat -Time "09:00"

Write-Host "`n작업이 등록되었습니다. 작업 스케줄러(taskschd.msc)에서 확인할 수 있습니다."
