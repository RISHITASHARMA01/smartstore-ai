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

### 1. Clone and configure

```bash
git clone https://github.com/RISHITASHARMA01/smartstore-ai.git
cd smartstore-ai
```

Copy and fill in the env file at the project root:

```bash
cp .env.example .env
```

Then edit `.env` — the two values you must set:

```env
SECRET_KEY=<run: python -c "import secrets; print(secrets.token_hex(32))">
GEMINI_API_KEY=your-gemini-api-key-here
```

### 2. Start PostgreSQL

```bash
docker run -d \
  --name smartstore-db \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=smartstore \
  -p 5432:5432 \
  postgres:15-alpine
```

### 3. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..
alembic upgrade head             # run migrations (alembic.ini is at project root)
cd backend
uvicorn app.main:app --reload --port 8000
```

API docs available at http://localhost:8000/docs

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — register a new account and log in.

---

## Docker Compose (one-command startup)

```bash
# Copy and fill in the env file first
cp .env.example .env   # then set SECRET_KEY and GEMINI_API_KEY

docker compose up --build
```

| Service  | URL |
|----------|-----|
| Frontend | http://localhost:3000 |
| Backend  | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

Run migrations inside the container after first start:

```bash
docker compose exec backend alembic upgrade head
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
