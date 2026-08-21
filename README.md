# YPADN Backend

Backend API for **Youth Political Awareness & Development Network (YPADN)**.

## Stack
- FastAPI
- SQLAlchemy
- PostgreSQL
- JWT authentication
- QR-code generation
- PDF membership-card generation
- Excel export
- Admin dashboard APIs

## Main API areas
- `/api/auth`
- `/api/members`
- `/api/admin`

## Registration numbers
New members receive IDs in the format:

`YPADN-000001`

## Environment
Configure:
- `DATABASE_URL`
- `SECRET_KEY`
- `ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `FRONTEND_ORIGINS`

Do not use the placeholder admin password in production.
# ypadn-backend
