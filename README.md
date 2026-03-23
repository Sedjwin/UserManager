# UserManager

Centralised user identity and JWT authentication service for the AI infrastructure stack. Other services call `GET /auth/validate` to verify tokens without maintaining their own user databases.

**Ports:** `8005` (internal) / `13376` (external, HTTPS via Caddy)

---

## Overview

- Single source of truth for user accounts across the stack
- JWT-based authentication (HS256, 12-hour tokens by default)
- Four roles: `demo` · `free` · `paid` · `admin`
- `GET /auth/validate` — lightweight token check for other services (returns `{valid: false}` on failure, never throws)
- Admin panel served from frontend build
- Default admin account seeded on first run

---

## Default Credentials

On first run, an admin account is created if no users exist:

| Field    | Default     |
|----------|-------------|
| Username | `admin`     |
| Password | `changeme`  |

**Change the password immediately via `.env` or the admin panel.**

---

## Configuration

Set via environment variables or `.env` file:

| Variable              | Default                                          | Description                    |
|-----------------------|--------------------------------------------------|--------------------------------|
| `SECRET_KEY`          | `change-me-in-production`                        | JWT signing key (min 32 chars) |
| `ADMIN_USERNAME`      | `admin`                                          | Initial admin username         |
| `ADMIN_PASSWORD`      | `changeme`                                       | Initial admin password         |
| `TOKEN_EXPIRE_HOURS`  | `12`                                             | JWT lifetime in hours          |
| `DATABASE_URL`        | `sqlite+aiosqlite:///./data/usermanager.db`      | Async SQLAlchemy connection    |
| `HOST`                | `127.0.0.1`                                      | Bind address                   |
| `PORT`                | `8005`                                           | Bind port                      |
| `DEFAULT_AGENT_IDS`   | `""`                                             | Comma-separated AgentManager UUIDs auto-granted to every new user on registration |

---

## API Reference

### Auth — `/auth`

| Method | Path               | Auth             | Description                                      |
|--------|--------------------|------------------|--------------------------------------------------|
| POST   | `/auth/login`      | None             | Login → JWT token                                |
| POST   | `/auth/register`   | None             | Public self-registration → JWT token (creates `free` user, auto-grants `DEFAULT_AGENT_IDS`) |
| GET    | `/auth/validate`   | Bearer (optional)| Validate token — used by other services          |
| GET    | `/auth/me`         | Bearer required  | Get current user's profile                       |
| GET    | `/health`          | None             | Service health check                             |

**Login request:**
```json
{ "username": "admin", "password": "changeme" }
```

**Login response (`TokenResponse`):**
```json
{
  "access_token": "eyJ0...",
  "token_type": "bearer",
  "user_id": 1,
  "username": "admin",
  "role": "admin"
}
```

**`GET /auth/validate`** — designed to be called by other microservices. Always returns 200; check the `valid` field.

```json
{ "valid": true, "user_id": 1, "username": "admin", "display_name": "Administrator", "role": "admin" }
```
or on any error (expired, missing, invalid):
```json
{ "valid": false }
```

---

### User Management — `/users` (admin only unless noted)

| Method | Path              | Auth                  | Description                                          |
|--------|-------------------|-----------------------|------------------------------------------------------|
| GET    | `/users`          | Bearer + admin        | List all users                                       |
| POST   | `/users`          | Bearer + admin        | Create user (201)                                    |
| GET    | `/users/{id}`     | Bearer + admin or self| Get user by ID                                       |
| PUT    | `/users/{id}`     | Bearer + admin or self| Update user (self: display_name/password; admin: all)|
| DELETE | `/users/{id}`     | Bearer + admin        | Delete user (204) — cannot delete own account        |

**Create user request:**
```json
{
  "username": "alice",
  "password": "securepassword",
  "display_name": "Alice",
  "role": "free"
}
```

**User profile (`UserOut`):**
```json
{
  "id": 1,
  "username": "admin",
  "display_name": "Administrator",
  "role": "admin",
  "is_active": true,
  "created_at": "2026-01-01T00:00:00",
  "last_login": "2026-03-22T13:00:00"
}
```

**Update request** (all fields optional):
```json
{
  "display_name": "New Name",
  "password": "newpassword",
  "role": "paid",
  "is_active": true
}
```
`role` and `is_active` are admin-only fields.

---

**Register request:**
```json
{ "username": "alice", "password": "securepassword", "display_name": "Alice" }
```

Response is the same `TokenResponse` format as login. `DEFAULT_AGENT_IDS` are granted atomically at creation time.

---

### Agent Grants — `/users` (agent access control)

Controls which AgentManager agents each user can access. Admin manages all grants; users can read their own.

| Method | Path                                | Auth           | Description                                    |
|--------|-------------------------------------|----------------|------------------------------------------------|
| GET    | `/users/me/agents`                  | Bearer         | List current user's granted agent IDs          |
| GET    | `/users/{id}/agents`                | Bearer + admin | List any user's granted agent IDs              |
| POST   | `/users/{id}/agents`                | Bearer + admin | Grant an agent to a user                       |
| DELETE | `/users/{id}/agents/{agent_id}`     | Bearer + admin | Revoke an agent grant                          |

**Grant request:**
```json
{ "agent_id": "07255695-7f09-4907-922e-04168a483cd1" }
```

**`GET /users/me/agents` response:**
```json
["07255695-7f09-4907-922e-04168a483cd1", "other-agent-uuid"]
```

---

## Roles

| Role    | Rank | Description             |
|---------|------|-------------------------|
| `demo`  | 0    | Lowest privilege        |
| `free`  | 1    | Default for new users   |
| `paid`  | 2    | Higher tier             |
| `admin` | 3    | Full access             |

---

## Database Models

### UserAgentGrant

| Column       | Type     | Notes                                      |
|--------------|----------|--------------------------------------------|
| `id`         | int PK   | Auto-increment                             |
| `user_id`    | int FK   | References `users.id` (CASCADE delete)     |
| `agent_id`   | str(64)  | AgentManager UUID                          |
| `granted_at` | datetime | Server-generated                           |

### User

| Column            | Type      | Notes                                   |
|-------------------|-----------|-----------------------------------------|
| `id`              | int PK    | Auto-increment                          |
| `username`        | str(64)   | Unique                                  |
| `hashed_password` | str(256)  | bcrypt (cost 12)                        |
| `display_name`    | str(128)  | Nullable                                |
| `role`            | str(16)   | `demo` / `free` / `paid` / `admin`     |
| `is_active`       | bool      | False = soft-deactivated (cannot login) |
| `created_at`      | datetime  | UTC, server-generated                   |
| `last_login`      | datetime  | Nullable, updated on each login         |

---

## Running

```bash
cd UserManager
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8005

# production
sudo systemctl start usermanager
sudo journalctl -u usermanager -f
```
