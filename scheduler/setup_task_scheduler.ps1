<#
.SYNOPSIS
    나눔보청기 순위 추적 크롤러를 Windows Task Scheduler에 등록한다.

.DESCRIPTION
    아래 두 작업을 평일(월~금) 기준으로 등록한다.
      - HearKorea_Schedule_Notify : 매일 09:00, 오늘의 스케줄 카톡 알림
      - HearKorea_Rank_Crawl      : 매일 10:00, 순위 조회 + Excel 저장 + 카톡 알림

.NOTES
    반드시 "관리자 권한"으로 PowerShell을 실행한 뒤 이 스크립트를 실행하세요.
    예) 이 폴더에서: powershell -ExecutionPolicy Bypass -File .\setup_task_scheduler.ps1
#>

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$NotifyBat = Join-Path $ProjectRoot "scheduler\run_notify.bat"
$CrawlBat = Join-Path $ProjectRoot "scheduler\run_crawl.bat"

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

Register-DailyWeekdayTask -TaskName "HearKorea_Schedule_Notify" -ScriptPath $NotifyBat -Time "09:00"
Register-DailyWeekdayTask -TaskName "HearKorea_Rank_Crawl" -ScriptPath $CrawlBat -Time "10:00"

Write-Host "`n모든 작업이 등록되었습니다. 작업 스케줄러(taskschd.msc)에서 확인할 수 있습니다."
