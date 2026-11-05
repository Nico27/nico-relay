#!/bin/sh
# Every container starts here: migrate, optionally seed, then hand over to the
# process in CMD. Migrations run as the non-root user and are idempotent, so a
# restart is always safe.
#
#   SEED_ON_START=1      load seed.sql only when the database is empty
#   SEED_ON_START=reset  truncate and reload seed.sql (destructive)
#   unset / 0            never touch the data
set -eu

python -m relay.migrate

case "${SEED_ON_START:-0}" in
    1)
        python -m relay.seed --if-empty --seed "${SEED_PATH:-/app/seed.sql}"
        ;;
    reset)
        python -m relay.seed --reset --seed "${SEED_PATH:-/app/seed.sql}"
        ;;
esac

exec "$@"
