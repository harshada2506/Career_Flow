@echo off
echo Starting Career Flow Project...

:: Start Backend
start cmd /k "cd /d C:\careerflow\app\backend && venv\Scripts\activate && python -m uvicorn main:app --reload"

:: Wait few seconds for backend to start
timeout /t 3

:: Start Frontend Server
start cmd /k "cd /d C:\careerflow\app\templates && python -m http.server 5500"

:: Open Landing Page in Browser
timeout /t 2
start http://localhost:5500/landing.html

echo Project Started Successfully!
pause@echo off
echo Starting Career Flow...

:: Start Backend
start cmd /k "cd /d C:\careerflow\app\backend && venv\Scripts\activate && python -m uvicorn main:app --reload"

:: Wait for backend
timeout /t 3

:: Start Frontend
start cmd /k "cd /d C:\careerflow\app\templates && python -m http.server 5500"

:: Wait for frontend
timeout /t 2

:: Open your correct file
start http://localhost:5500/landingpage.html

echo Project Started!
pause