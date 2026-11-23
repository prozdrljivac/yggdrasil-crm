#!/bin/bash
set -eu

# Keycloak substitutes these into JSON before parsing it.
for name in LOCAL_OWNER_PASSWORD LOCAL_NONOWNER_PASSWORD LOCAL_CRM_CLIENT_SECRET; do
  value="${!name:-}"
  if [[ ! "$value" =~ ^[A-Za-z0-9_-]{16,128}$ ]]; then
    printf '%s must contain 16-128 letters, digits, underscores, or hyphens.\n' "$name" >&2
    exit 1
  fi
done

exec /opt/keycloak/bin/kc.sh "$@"
