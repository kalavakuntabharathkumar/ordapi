# API notes

All routes are documented by FastAPI at `/docs`. List endpoints accept bounded pagination (`offset`, `limit`). Product list supports `q`; order list supports `status`. Order creation validates inventory before decrementing stock and computes totals from stored product prices. For production, add authentication/authorization, migrations, audit events, idempotency keys, and concurrency-safe stock updates/transactions.
