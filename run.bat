@echo off
echo Starting Internal IT Support Agent...
echo.

echo Step 1: Starting Backend...
cd backend
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt
if not exist .env (
    echo WARNING: .env file not found. Please create .env with GROQ_API_KEY
    echo Copying .env.example to .env...
    copy ..\.env.example .env
    echo Please edit .env and add your GROQ_API_KEY
    pause
)
start "Backend Server" cmd /k "python main.py"
cd ..

echo Step 2: Starting Frontend...
cd frontend
if not exist node_modules (
    echo Installing frontend dependencies...
    call npm install
)
start "Frontend Server" cmd /k "npm run dev"
cd ..

echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to close this window (servers will continue running)...
pause
