cat << 'EOF' > iniciar_analizador.bat
@echo off
title Football Stats Analyzer
cd /d "%~dp0"
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8000"
python -m uvicorn app:app
EOF