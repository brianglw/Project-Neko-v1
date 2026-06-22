@echo off
echo Starting both frontend and backend development servers...
start cmd /k "cd frontend && npm run dev"
start cmd /k "cd backend && .venv\Scripts\activate && python -m uvicorn server:app --reload"