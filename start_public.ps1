Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "    Starting SentinelFlow SOC Public Tunnel...     " -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

Write-Host "[1/2] Starting Uvicorn API server in a separate process..." -ForegroundColor Gray
Start-Process powershell -ArgumentList "-NoExit", "-Command", "C:\Users\91928\AppData\Local\Python\pythoncore-3.14-64\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000"

Write-Host "[2/2] Launching ngrok tunnel on port 8000..." -ForegroundColor Gray
Write-Host "👉 Copy the HTTPS URL (e.g., https://xxxx.ngrok-free.app) from the display below and share it!" -ForegroundColor Green
Write-Host ""
ngrok http 8000
