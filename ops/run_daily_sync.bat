@echo off
REM 매일 새벽 2시, TourAPI 시설 배치 적재를 실행한다 (Windows 작업 스케줄러에서 호출).
REM 이미 적재된 content_id는 자동 skip되고, 그날의 API 쿼터를 다 쓰면 스크립트가
REM 스스로 깔끔하게 멈춘다 - 별도 진행 상태 관리 없이 매일 그대로 재실행하면 이어서 진행됨.
REM Docker Desktop이 켜져 있어야 동작한다 (Docker Desktop 설정에서 로그인 시 자동 시작 필요).

setlocal

set PROJECT_DIR=C:\Users\erun2\ongil
set LOG_FILE=%PROJECT_DIR%\logs\sync_facilities.log

cd /d "%PROJECT_DIR%"

echo ==== %date% %time% ==== >> "%LOG_FILE%"
docker compose run --rm api python -m app.scripts.sync_facilities >> "%LOG_FILE%" 2>&1
echo exit code %errorlevel% >> "%LOG_FILE%"

endlocal
