# Local development

This is a local development shell, not a production deployment.

## Prerequisites

Install the pinned tools described in the [backend README](../server/README.md)
and [web client README](../client/web/README.md). Also install Git,
[Task 3.54.0](https://github.com/go-task/task/releases/tag/v3.54.0), Docker with
Compose v2, and curl with AWS SigV4 support. Use a POSIX shell or WSL2.

Start Docker before running infrastructure commands. Tests do not need its daemon.
Follow the [dependency installation rules](../AGENTS.md#dependency-installation-and-updates)
before installing tools or changing dependency versions.

## Start

Run these commands from the repository root:

```sh
nvm use 24.22.3  # If you use nvm.
task setup
task infra:up
```

Setup audits and installs locked dependencies. It creates `.env` from
`.env.example` only if `.env` does not exist; it does not install global tools.
Keep an existing `.env` aligned with the required keys in `.env.example`.
Credentials and host ports have one source in `.env`; image pins, loopback
bindings, and security controls stay in Compose.

Run each process in a separate terminal:

```sh
task api
task web
task worker
```

Open <http://127.0.0.1:5173>. The page should say **Local API is running.**
The API and web client can also run without Docker.

## Check and stop

```sh
task check         # Formatting, lint, types, tests, build, Compose validation.
task audit         # Dependency advisories; needs internet access.
task infra:check   # Database, broker, PDF service, signed and unsigned S3 access.
task worker:check  # Requires a running worker.
task infra:down    # Stop services; keep local data.
```

Stop foreground processes with Ctrl+C. The Compose CLI is needed for
`task check`, but Docker services, Doppler, and real credentials are not.
Compose automatically reads root `.env`; run `task setup` first to create it.
Automated configuration tests use isolated fictional settings.

## Scoped commands

Run these from the repository root. Commands without a scope run all relevant tasks.

| Action             | All                 | Web only                | Server only                |
| ------------------ | ------------------- | ----------------------- | -------------------------- |
| Format files       | `task format`       | `task format:web`       | `task format:server`       |
| Check formatting   | `task format:check` | `task format:web:check` | `task format:server:check` |
| Lint               | `task lint`         | `task lint:web`         | `task lint:server`         |
| Check types        | `task typecheck`    | `task typecheck:web`    | `task typecheck:server`    |
| Test               | `task test`         | `task test:web`         | `task test:server`         |
| Audit dependencies | `task audit`        | `task audit:web`        | `task audit:server`        |

`task format:shared` formats documents and configuration outside `server/` and
`client/web/`; `task format:shared:check` checks them without changes.
`task build` only builds the web client; there is no backend build task yet.

## Safety and help

Use fictional records and local credentials only. Never inject production
credentials, use this setup on a shared server, or expose its ports publicly.
Other users and processes on your computer can access local ports. Keep `.env`
out of Git. Shell variables override its values in both Compose and the app.

Service data stays in named volumes. `docker compose down --volumes` permanently
deletes all local service data; do not use it for routine shutdown. Changing
PostgreSQL or RabbitMQ credentials in `.env` does not change credentials already
stored in existing volumes.

See the [backend README](../server/README.md) for services, environment variables,
Doppler, and API troubleshooting. See the [web client README](../client/web/README.md)
for frontend commands and connection troubleshooting. Use `task --list` to see
all shared commands.
