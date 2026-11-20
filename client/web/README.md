# Web client

The React web client currently shows local API availability. Business screens and
owner login are not implemented yet.

## Layout

- `src/`: application code and component tests.
- `package.json`, `pnpm-lock.yaml`: pinned dependencies and scripts.
- `pnpm-workspace.yaml`: install security settings for this standalone project;
  it does not include additional packages.
- `.nvmrc`: pinned Node version.
- `node_modules/`, `dist/`: generated dependencies and build output; excluded
  from Git.

All Node settings and dependencies live here, not at the repository root.

## Tools and setup

Use [Node.js 24.22.3 LTS](https://nodejs.org/en/blog/release/v24.22.3) and
[pnpm 12.20.0](https://registry.npmjs.org/pnpm).
Follow the [dependency installation rules](../../AGENTS.md#dependency-installation-and-updates)
before installing or updating tools.

With an existing nvm installation, run from `client/web/`:

```sh
nvm install 24.22.3
nvm use
```

With a reviewed Node/npm installation, install the pinned pnpm:

```sh
npm install --global --ignore-scripts --include=optional pnpm@12.20.0
```

pnpm has only exact-version native platform optional dependencies. Confirm that
your platform's `@pnpm/exe.*@12.20.0` package installed before first use;
otherwise its wrapper can download the binary at startup.

For full setup, use the [local development guide](../../docs/local-development.md).
For frontend-only setup, run from `client/web/`:

```sh
pnpm audit
pnpm install --frozen-lockfile
```

This needs internet access and preserves the lockfile. Dependency build scripts
have no approvals. Do not enable all builds or bypass the seven-day age rule.

## Run and check

From `client/web/`:

```sh
pnpm dev
```

Open <http://127.0.0.1:5173>. Vite forwards `/api` to the backend at
`http://127.0.0.1:8000`. No broad CORS exception is needed.
Start the backend separately to see **Local API is running.**

```sh
pnpm format:check
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

Component tests cover API progress, success, failures, invalid responses, and
request cancellation. They need no running backend, Docker, Doppler, or secrets.
Browser end-to-end and mutation tests are not configured yet.

From the repository root, use `task format:web`, `task format:web:check`,
`task lint:web`, `task typecheck:web`, `task test:web`, or `task audit:web`
to target only this client.

Frontend formatting commands cover this directory. Root `task format` and
`task format:check` include backend and shared files. Root `task check`
checks both the backend and frontend.

## Safety and troubleshooting

- Never put secrets in browser code or `VITE_` variables; Vite can bundle them
  into browser assets.
- **Wrong Node version:** run `nvm use` here, then root `task tools`.
- **API unavailable:** start root `task api`, check its output, then reload the
  page. See the [backend README](../../server/README.md) for the API reference.
- **Port already used:** stop the conflicting process; keep loopback bindings.
- **Age or audit failure:** stop and follow the dependency installation rules rather than
  changing security settings or running automatic audit fixes.
