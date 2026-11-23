# Backend

The Python backend provides the API and Celery worker. Business records, owner
login, storage access, migrations, and document tasks are not implemented yet.

## Layout

- `src/`: application package, including API, settings, and worker entry points.
- `tests/`: backend tests.
- `pyproject.toml`, `uv.lock`: Python dependencies and tool settings.
- `.python-version`: pinned Python version.
- `.venv/`: generated virtual environment; excluded from Git.

## Tools and setup

Use [Python 3.14.10](https://www.python.org/downloads/release/python-31410/) and
[uv 0.13.7](https://pypi.org/pypi/uv/0.13.7/json).
Follow the [dependency installation rules](../AGENTS.md#dependency-installation-and-updates) and
[uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).
Do not use floating versions or pipe downloaded scripts into a shell.

If Python is missing, `uv python install 3.14.10` can install it. Verify the
runtime artifact's release date and checksum first; package-age settings do not
cover runtime downloads.

For full setup, use the [local development guide](../docs/local-development.md).
For backend-only setup, run from `server/`:

```sh
uv audit --locked
uv sync --locked --no-build
if [ ! -f ../.env ]; then cp ../.env.example ../.env; fi
```

This installs locked versions without third-party source builds. It needs
internet access and compatible wheels. Do not commit `.venv/` or `.env`.

## Run and check

From `server/`, run each long-running process in its own terminal:

```sh
uv run --locked --no-sync --env-file ../.env uvicorn src.api:app --host 127.0.0.1 --port 8000 --reload
uv run --locked --no-sync --env-file ../.env celery -A src.worker:app worker --loglevel=INFO --concurrency=1
```

For the API reference, open the [generated OpenAPI schema](http://127.0.0.1:8000/openapi.json)
after starting the API. The worker requires local RabbitMQ and accepts JSON only;
it has no document tasks yet.

```sh
uv run --locked --no-sync ruff format --check .
uv run --locked --no-sync ruff check .
uv run --locked --no-sync mypy
uv run --locked --no-sync pytest
```

From the repository root, use `task format:server`, `task format:server:check`,
`task lint:server`, `task typecheck:server`, `task test:server`, or
`task audit:server` to target only the backend. Backend formatting also checks
its documents with the web client's installed Prettier; Python-only formatting
can use the uv commands above.

Tests need no external services or secrets. The pinned Starlette test client
supports HTTPX 0.28.1 but emits its upstream deprecation warning.

## Local infrastructure

Manage local development infrastructure from the repository root with `task infra:up`,
`task infra:check`, `task infra:logs`, and `task infra:down`.

| Service             | Host endpoint          | Local identity                   |
| ------------------- | ---------------------- | -------------------------------- |
| PostgreSQL          | 127.0.0.1:5432         | Database/user: `yggdrasil_local` |
| RabbitMQ            | 127.0.0.1:5672         | User/vhost: `yggdrasil_local`    |
| RabbitMQ management | http://127.0.0.1:15672 | Same local RabbitMQ user         |
| Gotenberg           | http://127.0.0.1:3000  | Local conversion service         |
| SeaweedFS S3        | http://127.0.0.1:8333  | Bucket: `yggdrasil-local`        |
| Keycloak            | http://127.0.0.1:8081  | Fictional local realm            |

See the [local Keycloak guide](../infra/keycloak/README.md) for fixture accounts,
MFA checks, clock requirements, and the Keycloak-only reset. This infrastructure
does not implement CRM authentication or owner authorization.

Root `.env` supplies local credentials and host ports to both Compose and the
application. [Example settings](../.env.example) list all required keys. The table
above shows example defaults, not fixed host ports. Compose passes only the
variables each container needs; it does not forward the entire file.

The backend builds its broker URL from `YGGDRASIL_RABBITMQ_USER`,
`YGGDRASIL_RABBITMQ_PASSWORD`, `YGGDRASIL_RABBITMQ_VHOST`, and
`YGGDRASIL_RABBITMQ_PORT`. Credentials and the vhost are URL-encoded separately.
PostgreSQL, S3, and Gotenberg settings are reserved for future application
integration.

PostgreSQL 18 uses the volume path `/var/lib/postgresql`. Its local bootstrap
user is a superuser; restricted application roles and migrations must be defined
before storage work. PostgreSQL and RabbitMQ initialization credentials only
apply to fresh volumes. Editing `.env` does not rotate existing credentials.
Update them explicitly, or delete disposable local volumes only after accepting
the data loss.

SeaweedFS creates the bucket and requires signed S3 access. IAM, WebDAV, the admin
UI, Iceberg, and Lance are disabled. Its health check checks the master;
`task infra:check` checks signed and unsigned bucket access inside the storage
container, using its configured credentials. It does not print those credentials.

Gotenberg disables JavaScript, remote downloads, webhooks, and LibreOffice
routes. Outbound private/public IP checks stay enabled. Invoice rendering still
needs separate acceptance tests.

Services use separate networks. Gotenberg and SeaweedFS use internal networks,
which do not block every path to host services. Verify loopback publishing on
your Docker installation. Do not weaken isolation to fix an access problem.
Keep these services local. Package dependency audits do not scan operating-system
packages inside container images.

## Settings and Doppler

The app reads environment variables, not Doppler's API. Root `.env` supplies
fictional local settings. Both Compose and uv give existing shell environment
variables precedence over `.env`. Single-quote dotenv values containing `$` to
keep the dollar sign literal. Never load this file with `source` or print resolved
Compose configuration when it contains secrets. A dotenv file is not a security
boundary; keep it out of Git.

Routine setup and tests do not need Doppler. If a development configuration has
been prepared, use [Doppler CLI 3.77.1](https://docs.doppler.com/docs/cli).
From the repository root:

```sh
doppler run --project YOUR_DEV_PROJECT --config YOUR_DEV_CONFIG -- task api
doppler run --project YOUR_DEV_PROJECT --config YOUR_DEV_CONFIG -- task worker
```

Replace the placeholders with agreed development values. Use local service
credentials only. Never use a production configuration, pass Doppler tokens to
containers, print settings, or commit secrets.

## Troubleshooting

- **Docker connection failed:** start Docker Desktop or the Docker daemon.
- **API unavailable:** check server output and confirm that the API process is
  running on its configured port.
- **Worker cannot connect:** check `docker compose ps` and
  `task infra:logs` from the repository root. Confirm that root `.env` points
  to the local RabbitMQ vhost.
- **Missing settings:** compare root `.env` with `.env.example` and add missing
  keys. `task setup` preserves existing files and does not migrate old settings.
- **Port already used:** stop the conflicting process; keep loopback bindings.
- **Age or audit failure:** stop and follow the dependency installation rules. Do not bypass
  the checks or use automatic audit fixes.
