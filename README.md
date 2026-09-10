# Employee Training Management System

Production-ready starter for an employee training management portal using **React + TypeScript + Tailwind CSS + Flask + MongoDB**.

## 1. Requirements
- Python 3.10+
- Node.js 20+
- MongoDB 6+

## 2. Backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
python run.py
```
Backend runs on `http://localhost:5000`.

Set `MONGO_URI`, `MONGO_DB`, `JWT_SECRET`, and `FRONTEND_ORIGIN` in `.env`.

## 3. Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend runs on the Vite URL shown in the terminal, normally `http://localhost:5173`.

For a production build:
```bash
npm run build
npm run preview
```

## 4. Demo accounts
The development seed creates these accounts when the database is empty:
- `admin` / `Admin@123` — HR Admin
- `manager` / `Manager@123` — Manager, Production
- `employee` / `Employee@123` — Employee, QA / Quality

Change or remove demo credentials before production use.

## 5. Main modules
- Role-based login and access control
- HR employee and department management
- Training creation, assignment, scheduling and completion
- Department-restricted manager access
- Attendance tracking and bulk attendance
- Employee feedback form based on the supplied reference form
- 3-month effectiveness evaluation
- Analytics dashboard
- CSV reports
- In-app notifications
- Responsive desktop/tablet/mobile UI
- Logo placeholder areas ready for the company logo

## 6. Logo
Replace the placeholder component/content in `frontend/src/components/LogoPlaceholder.tsx` and the feedback-page logo area with the final company logo when available.

## 7. API
All application APIs are under `/api`. Health check:
`GET /api/health`
