#!/bin/sh
set -eu

if [ "$#" -gt 0 ]; then
  exec "$@"
fi

# Trust X-Forwarded-* from nobody by default.
#
# A non-empty value makes uvicorn REWRITE the peer address from X-Forwarded-For
# before any application code runs. Defaulting this to 127.0.0.1 is unsafe here:
# the API binds to loopback behind a same-host reverse proxy, so every request
# arrives from 127.0.0.1 and would be trusted — letting any caller forge their
# own source address and reset per-IP rate limits at will.
#
# Set this only to the address of a proxy you control, and make sure that proxy
# OVERWRITES X-Forwarded-For (nginx: proxy_set_header X-Forwarded-For $remote_addr)
# rather than appending to a client-supplied value. Keep it in sync with
# RATE_LIMIT_TRUSTED_PROXIES, which governs the same trust decision in-app.
FORWARDED_ALLOW_IPS="${FORWARDED_ALLOW_IPS:-}"

exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --proxy-headers \
  --forwarded-allow-ips="${FORWARDED_ALLOW_IPS}"
