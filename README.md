# Test Task Monorepo

This repository contains a **FastAPI + PostgreSQL** backend and a **React** frontend, organized as a monorepo. It implements the requirements from the test task here:  
https://gist.github.com/nikita-hooligapps/c7c456a0e1f640e6afe7417701e5eb37

- **frontend/**: React (TypeScript) app  
- **server/**: FastAPI service, Alembic migrations, seeding logic, OpenTelemetry tracing  
- **docker-compose.yml**: orchestrates Postgres, Jaeger, backend, and frontend  

---

## Getting Started

1. **Clone** the repository:
   ```
   git clone https://github.com/NikitaAstakhov/test-fullstack.git
   cd your-repo
   ```

2. **Build and run** everything with Docker:
   ```
   docker-compose up --build
   ```
   On the first run, the backend will apply migrations and seed **2 million** fake submissions. This takes roughly 10 seconds.

---

## After Startup

- **Frontend**:  
  Open `http://localhost:3000` to use the form at `/submit` or view history at `/history`.

- **Tracing & Metrics**:  
  Open Jaeger at `http://localhost:16686` to see request spans and custom database metrics.

- **API Endpoints** (backend on port 8000):  
  - `POST /submit`  
    - Accepts `{ "date": "YYYY-MM-DD", "first_name": "Foo", "last_name": "Bar" }`  
    - Simulates a random delay, inserts one row, and returns 2–5 objects of the form `{ date, name }`
  - `GET /history`  
    - Returns the last 10 submissions with a `count` of earlier entries per `(first_name, last_name)`

---

## Project Structure

```
.
├── frontend/           # React application
│   ├── src/
│   ├── public/
│   └── package.json
├── server/             # FastAPI + Alembic + seed + tracing
│   ├── app/
│   ├── db/
│   ├── alembic.ini
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml
└── README.md
```

- **server/app/**: FastAPI code, routers, Pydantic schemas, OpenTelemetry setup  
- **server/db/**: SQLAlchemy models, CRUD, Alembic migrations, seed logic  
- **frontend/src/**: pages, components, API service, data types  

---

## Notes

- On first startup, seeding 2 million rows is done via concurrent batch inserts and usually finishes in under 10 seconds.  
- If you restart without removing the Postgres volume, seeding will be skipped (table already has ≥ 100 000 rows).

Feel free to explore, and check Jaeger for detailed traces!
