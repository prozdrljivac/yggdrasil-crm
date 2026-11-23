# Local Keycloak

This is disposable identity infrastructure for development and tests. It does not
implement CRM login, CRM sessions, or CRM owner authorization. Do not use it in
production or connect it to production identity providers.

## Start and check

From the repository root, prepare the tools and settings using the
[local development guide](../../docs/local-development.md), then run:

```sh
task keycloak:up
task keycloak:check
```

`task infra:up` also starts Keycloak. `task keycloak:check` checks clock alignment
and local OpenID Connect discovery; it does not prove browser MFA or CRM access.

The default host port is 8081; change `YGGDRASIL_KEYCLOAK_PORT` in root `.env`
if needed. Use the same host and port consistently:

- [Account console](http://127.0.0.1:8081/realms/huginn-muninn-local/account/)
- [Admin console](http://127.0.0.1:8081/admin/)

Only the app port is published, bound to `127.0.0.1`. Management port 9000 stays
unpublished. The dedicated bridge network has no other application containers
but allows outbound traffic; it is not an air gap.

## Fictional accounts

Realm: `huginn-muninn-local`.

| Account           | Username           | Password setting                       | Stable subject identifier              |
| ----------------- | ------------------ | -------------------------------------- | -------------------------------------- |
| Owner fixture     | `fixture-owner`    | `YGGDRASIL_KEYCLOAK_OWNER_PASSWORD`    | `7ecb6b4c-d775-4c64-a289-d97bd4184411` |
| Non-owner fixture | `fixture-nonowner` | `YGGDRASIL_KEYCLOAK_NONOWNER_PASSWORD` | `15633bb8-58f9-444d-b14e-6bd3973b7422` |

The issuer is `http://127.0.0.1:<configured-port>/realms/huginn-muninn-local`.
These labels do not grant or deny CRM access. Both users may sign into their own
Keycloak account console. Neither has CRM permissions or administrator roles.

Root `.env.example` contains public fictional defaults; root `.env` supplies
actual local values. The administrator has separate
`YGGDRASIL_KEYCLOAK_ADMIN_USER` and `YGGDRASIL_KEYCLOAK_ADMIN_PASSWORD` settings
in the `master` realm. Do not use administrator credentials in the CRM client.

Realm-import passwords and the client secret must contain 16–128 letters,
digits, underscores, or hyphens. Startup rejects other characters before
Keycloak expands the JSON placeholders. Do not put real credentials in the seed.

## Browser login and MFA checks

Use a separate browser profile or private session for each fixture:

1. Open the account console and sign in with the fixture username and password.
2. Confirm that first login requires authenticator enrollment. Scan the displayed
   QR code, or use **Unable to scan?** to enter the key in an authenticator.
3. Submit a current code and a device label. Confirm that the account console
   opens for the correct fictional user.
4. Sign out. Sign in again and confirm that password alone is insufficient.
5. Enter an incorrect one-time code. Confirm that it is rejected. Then enter a
   current valid code and confirm access.
6. Repeat for the other fixture. Check narrow layouts and keyboard navigation.

Keep the host, Docker VM, and authenticator clocks synchronized. If valid codes
are rejected, run `task keycloak:check`. Restart or resynchronize Docker Desktop
when its clock drifts. Do not relax the MFA policy or increase the OTP window.

Account-console login tests Keycloak only. The confidential `yggdrasil-crm`
client requires S256 PKCE and has password grants, implicit flow, and service
accounts disabled. Its redirect and origin lists are empty until the CRM
callback is implemented. Do not add wildcard redirects or expose its secret
to browser code.

## Inspect and restart

Use the admin console to inspect the fixture identifiers, client settings,
required password/OTP flow, and self-account permissions. Do not paste tokens
into external decoder sites or publish tokens, passwords, or authenticator keys.

```sh
task keycloak:logs
docker compose up --detach --no-deps --force-recreate --wait keycloak
```

Recreating the container keeps user IDs and enrolled authenticators in the named
data volume. Startup import skips an existing realm. Editing the seed or `.env`
does not update existing users, client secrets, or administrator credentials.

## Reset only Keycloak

```sh
task keycloak:reset
```

This asks for confirmation, stops and removes only the Keycloak container,
deletes only its dedicated Compose-managed data volume, and starts it again.
It refuses an external or shared data volume.

Reset permanently removes local accounts, sessions, signing keys, and MFA
enrollments. The seed restores the fictional accounts with the same identifiers;
both users must enroll authenticators again. PostgreSQL, RabbitMQ, and storage
volumes are not reset. Do not use `docker compose down --volumes` for this task.
