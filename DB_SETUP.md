# Database Connection Setup & Troubleshooting

## Problem
`alembic upgrade head` was hanging because **PostgreSQL connection times out**. Test shows:
```
connection to server at "localhost" (127.0.0.1), port 5432 failed: timeout expired
```

## Configuration Done
- **.env**: `DATABASE_URL=postgresql://admin:spade@localhost:5432/recruiter_ai_db` (fixed spaces)
- **alembic.ini**: Same URL with `?connect_timeout=10` (fails fast instead of hanging)
- **app/database.py**: Loads dotenv for consistent DATABASE_URL
- **alembic/env.py**: Loads dotenv, adds connect_args timeout

## Root Cause
Port 5432 is open (nc succeeds) but **PostgreSQL handshake times out**. Possible causes:

1. **SSH tunnel not running** – Start before running alembic:
   ```bash
   ssh -L 5432:localhost:5432 root@157.180.26.18
   ```
   If port 5432 is busy, use a different local port:
   ```bash
   ssh -L 5433:localhost:5432 root@157.180.26.18
   ```
   Then set `DATABASE_URL=postgresql://admin:spade@localhost:5433/recruiter_ai_db`

2. **PostgreSQL on server not accepting connections** – Check on server:
   ```bash
   sudo systemctl status postgresql
   sudo -u postgres psql -c "SELECT 1"
   ```

3. **pg_hba.conf** – Ensure local connections are allowed on the server.

## Quick Test
```bash
conda activate ai_interviewer
python test_db_minimal.py
```
- If OK: Run `alembic upgrade head`
- If timeout: Fix SSH tunnel or server PostgreSQL first.
