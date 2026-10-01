# Order and Inventory Backend API

A runnable starter implementation for a retail distributor: FastAPI, SQLAlchemy, PostgreSQL-ready configuration, optional Redis cache, Docker, and pytest.

## Run locally
1. `python -m venv .venv` then activate it.
2. `pip install -r requirements.txt`
3. `uvicorn app.main:app --reload`
4. Open `http://127.0.0.1:8000/docs`.

By default it uses SQLite for a zero-setup demo. Set `DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/defcast` for PostgreSQL. Redis caching is enabled when `REDIS_URL` is set and Redis is reachable; otherwise the API safely runs without it.

## Main routes
- `GET/POST /products`, `GET/PATCH/DELETE /products/{id}`
- `GET/POST /orders`, `GET /orders/{id}`, `PATCH /orders/{id}/status`
- `GET /health`

This is a starter repo, not evidence that the resume metrics in any accompanying description have been measured. Load tests, auth, roles, migrations, and production monitoring should be added before production use.
