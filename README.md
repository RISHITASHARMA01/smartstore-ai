# SmartStore AI

An AI-powered inventory management system built with FastAPI + React. Manage products, suppliers, and purchase orders — with Gemini AI chat, invoice OCR parsing, demand forecasting, and live analytics.

---

## Features

| Area | What it does |
|------|-------------|
| **Products** | Full CRUD, low-stock badges, per-product detail page |
| **Suppliers** | Supplier directory with category tags and lead times |
| **Purchase Orders** | Create POs with line items, track status (Draft → Sent → Acknowledged → Received) |
| **Invoice OCR** | Upload a photo/PDF of an invoice → Gemini Vision extracts supplier, date, and line items → confirm to update stock |
| **AI Chat** | Floating chat panel powered by Gemini 2.5 Flash with 4 live DB tools: low stock, product detail, PO history, expiry alerts |
| **Demand Forecast** | 7-day exponential-smoothing forecast per product, rendered as a line chart |
| **Stock Adjustments** | Record sales, restocks, write-offs, and manual corrections with full history log |
| **Reports & Analytics** | Bar chart + pie chart by category, stock movement history, low-stock table, expiry table, PO status breakdown |
| **JWT Auth** | Register / login / refresh tokens, all routes protected |

---

## Tech Stack

**Backend**
- Python 3.11 + FastAPI
- PostgreSQL + SQLAlchemy ORM + Alembic migrations
- Google Gemini API (`google-genai` v2.x) — chat function calling + vision OCR
- Exponential smoothing for demand forecasting (no external ML library)

**Frontend**
- React 19 + Vite
- Tailwind CSS
- Zustand (auth state)
- React Router v7
- Recharts (forecast + analytics charts)
- react-hot-toast

---

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker (for PostgreSQL, or bring your own)
- A [Google Gemini API key](https://aistudio.google.com/app/apikey)

---

## Local Setup

> **Windows users:** A one-command setup script is available — see [PowerShell Quick Start](#powershell-quick-start-windows) below, or follow the step-by-step instructions with the PowerShell equivalents shown in each section.

### 1. Clone and configure

**bash / macOS / Linux**
```bash
git clone https://github.com/RISHITASHARMA01/smartstore-ai.git
cd smartstore-ai
cp .env.example .env
```

**PowerShell (Windows)**
```powershell
git clone https://github.com/RISHITASHARMA01/smartstore-ai.git
Set-Location smartstore-ai
Copy-Item .env.example .env
```

Then edit `.env` — the two values you must set:

```env
SECRET_KEY=<generate below>
GEMINI_API_KEY=your-gemini-api-key-here
```

Generate a secure `SECRET_KEY`:

**bash**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**PowerShell**
```powershell
.\scripts\generate-secret.ps1
```

---

### 2. Start PostgreSQL

**bash**
```bash
docker run -d \
  --name smartstore-db \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=smartstore \
  -p 5432:5432 \
  postgres:15-alpine
```

**PowerShell**
```powershell
docker run -d `
  --name smartstore-db `
  -e POSTGRES_PASSWORD=password `
  -e POSTGRES_DB=smartstore `
  -p 5432:5432 `
  postgres:15-alpine
```

---

### 3. Backend

**bash**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..
alembic upgrade head
cd backend
uvicorn app.main:app --reload --port 8000
```

**PowerShell**
```powershell
Set-Location backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Set-Location ..
alembic upgrade head
Set-Location backend
uvicorn app.main:app --reload --port 8000
```

> If PowerShell blocks script execution, run once:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

API docs: http://localhost:8000/docs

---

### 4. Frontend

**bash**
```bash
cd frontend
npm install
npm run dev
```

**PowerShell**
```powershell
Set-Location frontend
npm install
npm run dev
```

Open http://localhost:5173 — register a new account and log in.

---

## PowerShell Quick Start (Windows)

One script handles the full setup — Python venv, dependencies, PostgreSQL container, migrations, and npm install:

```powershell
# Allow local scripts (one-time, first run only)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Full setup
.\scripts\setup.ps1

# Then start each server in a separate terminal:
.\scripts\start-backend.ps1
.\scripts\start-frontend.ps1
```

### Available PowerShell scripts

| Script | What it does |
|--------|-------------|
| `.\scripts\setup.ps1` | Full first-time setup — venv, pip install, PostgreSQL, migrations, npm install |
| `.\scripts\start-backend.ps1` | Start FastAPI backend with auto-reload on http://localhost:8000 |
| `.\scripts\start-frontend.ps1` | Start Vite dev server with HMR on http://localhost:5173 |
| `.\scripts\migrate.ps1` | Run `alembic upgrade head` (apply pending migrations) |
| `.\scripts\migrate.ps1 -Message "add_table"` | Generate a new Alembic migration |
| `.\scripts\generate-secret.ps1` | Generate a cryptographically secure `SECRET_KEY` |

---

## Docker Compose (one-command startup)

**bash**
```bash
cp .env.example .env   # set SECRET_KEY and GEMINI_API_KEY
docker compose up --build
```

**PowerShell**
```powershell
Copy-Item .env.example .env   # set SECRET_KEY and GEMINI_API_KEY
docker compose up --build
```

| Service  | URL |
|----------|-----|
| Frontend | http://localhost:3000 |
| Backend  | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

Run migrations inside the container after first start:

**bash / PowerShell**
```bash
docker compose exec backend alembic upgrade head
```

---

### Changing ports (if defaults are already in use)

If ports `3000` or `8000` are occupied on your machine, change the host-side port numbers in `docker-compose.yml` and update `.env` to match.

**Example — move frontend to 3001, backend to 8080:**

**bash**
```bash
# 1. Edit docker-compose.yml
sed -i 's/"3000:80"/"3001:80"/' docker-compose.yml
sed -i 's/"8000:8000"/"8080:8000"/' docker-compose.yml

# 2. Update .env
sed -i 's|VITE_API_URL=http://localhost:8000|VITE_API_URL=http://localhost:8080|' .env
sed -i 's|ALLOWED_ORIGINS=http://localhost:3000|ALLOWED_ORIGINS=http://localhost:3001|' .env

# 3. Rebuild and restart (Vite bakes VITE_API_URL at build time)
docker compose down
docker compose up --build -d
```

**PowerShell**
```powershell
# 1. Edit docker-compose.yml
(Get-Content docker-compose.yml) -replace '"3000:80"', '"3001:80"' `
  -replace '"8000:8000"', '"8080:8000"' |
  Set-Content docker-compose.yml

# 2. Update .env
(Get-Content .env) `
  -replace 'VITE_API_URL=http://localhost:8000', 'VITE_API_URL=http://localhost:8080' `
  -replace 'ALLOWED_ORIGINS=http://localhost:3000', 'ALLOWED_ORIGINS=http://localhost:3001' |
  Set-Content .env

# 3. Rebuild and restart (Vite bakes VITE_API_URL at build time)
docker compose down
docker compose up --build -d
```

Your app will then be at:

| Service  | URL |
|----------|-----|
| Frontend | http://localhost:3001 |
| Backend  | http://localhost:8080 |
| API Docs | http://localhost:8080/docs |

> **Only change the number before the colon.** The number after the colon is the internal container port — leave it as-is.

To find which ports are already in use:

**bash**
```bash
ss -tlnp | grep -E ':(3000|8000)'
```

**PowerShell**
```powershell
netstat -ano | Select-String ':3000|:8000'
```

---

## Project Structure

```
smartstore-ai/
├── backend/
│   ├── app/
│   │   ├── routers/          # FastAPI route handlers
│   │   │   ├── products.py   # CRUD + stock adjust + history
│   │   │   ├── suppliers.py
│   │   │   ├── purchase_orders.py
│   │   │   ├── invoices.py   # OCR parse + confirm
│   │   │   ├── ai.py         # Gemini chat with function calling
│   │   │   ├── forecast.py   # 7-day demand forecast
│   │   │   ├── dashboard.py  # Stats for dashboard cards
│   │   │   └── reports.py    # Analytics endpoints
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/
│   │   │   ├── ai_tools.py   # DB query functions exposed to Gemini
│   │   │   └── forecast.py   # Exponential smoothing logic
│   │   └── auth/             # JWT utilities + dependencies
│   ├── alembic/              # DB migrations
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/            # Dashboard, Products, Suppliers, POs, Invoices, Reports
│   │   ├── components/       # Layout, ChatPanel, ProductModal, StockAdjustModal
│   │   ├── api/              # Axios instance + typed helpers
│   │   └── store/            # Zustand auth store
│   └── Dockerfile
├── scripts/                  # PowerShell helper scripts (Windows)
│   ├── setup.ps1             # Full first-time setup
│   ├── start-backend.ps1     # Start FastAPI dev server
│   ├── start-frontend.ps1    # Start Vite dev server
│   ├── migrate.ps1           # Run / generate Alembic migrations
│   └── generate-secret.ps1  # Generate SECRET_KEY
├── docs/                     # Sample invoices for testing OCR
└── docker-compose.yml
```

---

## API Reference

Full interactive docs at `http://localhost:8000/docs` (Swagger UI).

Key endpoints:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Get access + refresh tokens |
| POST | `/auth/logout` | Revoke current token |
| GET | `/products/` | List products (search, category, low_stock filters) |
| POST | `/products/{id}/adjust` | Record sale / restock / write-off / adjustment |
| GET | `/products/{id}/history` | Stock movement log for a product |
| GET | `/products/{id}/forecast` | 7-day demand forecast |
| POST | `/invoices/parse` | Upload invoice image → Gemini OCR |
| POST | `/invoices/confirm/{id}` | Confirm parsed invoice → update stock |
| POST | `/ai/chat` | Gemini chat with inventory DB tools |
| GET | `/dashboard/stats` | Counts for dashboard cards |
| GET | `/reports/stock-by-category` | Stock grouped by category |
| GET | `/reports/low-stock` | Products below reorder threshold |
| GET | `/reports/expiring-soon` | Products expiring within 30 days |
| GET | `/reports/stock-history` | Daily restock/sale aggregates |

---

## Sample Invoice Testing

Two sample invoices are included in `docs/`:

- `docs/sample_invoice_1.txt` — Agro Supplies Co. (Rice, Oil, Sugar, Flour, Salt)
- `docs/sample_invoice_2.txt` — Fresh Dairy Distributors (Milk, Paneer, Butter, Curd, Ghee, Cheese)

Convert either to a PNG/JPG and upload via the Invoices → Upload Invoice page to test OCR.

---

## Built With

This project was built day-by-day as a 9-day milestone project:

| Day | Focus |
|-----|-------|
| 1–2 | React setup, auth UI, DB schema (8 tables) |
| 3 | Products CRUD |
| 4 | Suppliers CRUD |
| 5 | Purchase Orders with line items |
| 6 | JWT auth (register, login, refresh, /me) |
| 7 | Gemini AI chat (4 DB tools) + demand forecast |
| 8 | Invoice OCR with Gemini Vision |
| 9 | Reports & Analytics + Dashboard stats |
| 10 | Stock adjustments, Docker Compose, README |
