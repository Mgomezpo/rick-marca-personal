@echo off
echo ===================================================
echo   Iniciando RICK Multitenant Agent Engine
echo ===================================================
echo Servidor escuchando en http://localhost:8000
echo Swagger UI disponible en http://localhost:8000/docs
echo Webhook endpoint: http://localhost:8000/webhook
echo.
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
