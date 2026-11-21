# Hand_Drawn_animation

FastAPI backend + a standalone React login page (`frontend/login.html`).

## Run locally

1. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

2. Start PostgreSQL and Redis, then create `src/.env` (see `src/.env.example` for the
   variable names). A working local example is already present in `src/.env`;
   replace the JWT secret and mail credentials before deploying.

3. Start the API (from this folder):

   ```powershell
   uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
   ```

4. Start the e-mail worker so verification / reset links are delivered:

   ```powershell
   celery -A src.utils.celery.c_app worker --loglevel=info
   ```

5. Open the page:

   - <http://localhost:8000/login> (served by the API, same origin), or
   - open `frontend/login.html` directly from disk (CORS is enabled).

## Verify the connection

```powershell
python verify_connection.py
```

The script checks that every page action maps to a backend route, that CORS is
enabled, and exercises the API in-process. If the server is running it also
checks the live `/` and `/openapi.json` responses.

## Frontend → API mapping

| Page action | Endpoint |
| --- | --- |
| Create account | `POST /api/v1/users/register` |
| Log in | `POST /api/v1/users/login` |
| Sign out | `POST /api/v1/users/logout` |
| Forgot password | `POST /api/v1/users/forgot-password` |
| Reset password (link in e-mail) | `POST /api/v1/users/reset-password` |

The JWT pair is stored in `sessionStorage` by default, or in `localStorage` when
"Keep me signed in" is checked. Override the API address from the host page with
`window.HAND_DRAWN_API_BASE` if the backend is not on `localhost:8000`.

## Configuration

- `FRONTEND_URL` – base URL used in password-reset e-mails (default `http://localhost:8000/login`).
- `CORS_ORIGINS` – comma-separated list of browser origins allowed to call the API (`*` by default, fine for local development).
- `DOMAIN_NAME` – host used in e-mail verification links.
