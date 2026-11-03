#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${PROJECT_ROOT}/.env"

TEST_ROLE="moviely_test"
TEST_DATABASE="moviely_test"
DEV_DATABASE="moviely"

# ---------------------------------------------------------
# 1. Validate local configuration
# ---------------------------------------------------------

if [[ ! -f "${ENV_FILE}" ]]; then
    echo "ERROR: .env file not found." >&2
    exit 1
fi

for variable in POSTGRES_PASSWORD POSTGRES_TEST_PASSWORD; do
    if ! grep -q "^${variable}=." "${ENV_FILE}"; then
        echo "ERROR: ${variable} is missing or empty in .env" >&2
        exit 1
    fi
done

# Prevent shell tracing from exposing credentials.
if [[ "$-" == *x* ]]; then
    echo "ERROR: Do not run provisioning with shell tracing enabled." >&2
    exit 1
fi

echo "Moviely test database configuration: OK"

cd "${PROJECT_ROOT}"

# ---------------------------------------------------------
# 2. Select PostgreSQL environment
# ---------------------------------------------------------

PROVISION_TARGET="${MOVIELY_PROVISION_TARGET:-local}"

case "${PROVISION_TARGET}" in
local)
    COMPOSE_ARGS=(
        --env-file "${ENV_FILE}"
        -f compose.yaml
        -f deploy/local/compose.yaml
    )
    ;;

provision-check)
    COMPOSE_ARGS=(
        --env-file "${ENV_FILE}"
        -p moviely-provision-check
        -f tests/provisioning/compose.yaml
    )
    ;;

*)
    echo "ERROR: Unknown provisioning target: ${PROVISION_TARGET}" >&2
    exit 1
    ;;
esac

compose() {
    docker compose "${COMPOSE_ARGS[@]}" "$@"
}

echo "Provisioning target: ${PROVISION_TARGET}"

# ---------------------------------------------------------
# 3. PostgreSQL helpers
# ---------------------------------------------------------

# Execute SQL and return machine-readable output.
postgres_query() {
    compose exec -T db \
        psql -U moviely -d postgres \
        -v ON_ERROR_STOP=1 \
        -At -c "$1"
}

# Execute SQL supplied through standard input.
postgres_exec() {
    compose exec -T db \
        psql -U moviely -d postgres \
        -v ON_ERROR_STOP=1
}

# Return codes:
#   0 = object exists
#   1 = object does not exist
#   2 = database query failed
query_exists() {
    local sql="$1"
    local result

    if ! result="$(postgres_query "${sql}")"; then
        echo "ERROR: PostgreSQL existence query failed." >&2
        return 2
    fi

    case "${result}" in
    t) return 0 ;;
    f) return 1 ;;
    *)
        echo "ERROR: Unexpected PostgreSQL query result." >&2
        return 2
        ;;
    esac
}

role_exists() {
    query_exists "
        SELECT EXISTS (
            SELECT 1
            FROM pg_roles
            WHERE rolname = 'moviely_test'
        );
    "
}

database_exists() {
    query_exists "
        SELECT EXISTS (
            SELECT 1
            FROM pg_database
            WHERE datname = 'moviely_test'
        );
    "
}

# ---------------------------------------------------------
# 4. Provision restricted test role
# ---------------------------------------------------------

echo "Inspecting PostgreSQL test role..."

if role_exists; then
    echo "Test role already exists."
else
    status=$?

    if [[ "${status}" -ne 1 ]]; then
        echo "ERROR: Cannot safely determine whether the test role exists." >&2
        exit 1
    fi

    echo "Creating restricted PostgreSQL test role..."

    test_password="$(
        sed -n 's/^POSTGRES_TEST_PASSWORD=//p' "${ENV_FILE}"
    )"

    # The initial provisioning contract uses:
    # openssl rand -hex 24
    if [[ ! "${test_password}" =~ ^[[:xdigit:]]{48}$ ]]; then
        echo "ERROR: POSTGRES_TEST_PASSWORD must be a 48-character hexadecimal password." >&2
        exit 1
    fi

    # Send credentials through stdin rather than process arguments.
    # A hexadecimal password contains no SQL quoting characters.
    printf \
        "CREATE ROLE %s WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD '%s';\n" \
        "${TEST_ROLE}" \
        "${test_password}" | postgres_exec

    unset test_password

    echo "Restricted PostgreSQL test role created."
fi

# ---------------------------------------------------------
# 5. Provision test database
# ---------------------------------------------------------

echo "Inspecting PostgreSQL test database..."

if database_exists; then
    echo "Test database already exists."
else
    status=$?

    if [[ "${status}" -ne 1 ]]; then
        echo "ERROR: Cannot safely determine whether the test database exists." >&2
        exit 1
    fi

    echo "Creating test database..."

    compose exec -T db \
        createdb -U moviely \
        --owner="${TEST_ROLE}" \
        "${TEST_DATABASE}"

    echo "Test database created."
fi

# ---------------------------------------------------------
# 6. Protect development database
# ---------------------------------------------------------

echo "Enforcing development database access restrictions..."

postgres_query "
    REVOKE CONNECT ON DATABASE ${DEV_DATABASE} FROM PUBLIC;
" >/dev/null

echo "Development database access restrictions: OK"

# ---------------------------------------------------------
# 7. Validate database isolation
# ---------------------------------------------------------

echo "Validating PostgreSQL test database isolation..."

isolation_valid="$(postgres_query "
SELECT COALESCE((
    SELECT
        r.rolcanlogin
        AND NOT r.rolsuper
        AND NOT r.rolcreatedb
        AND NOT r.rolcreaterole
        AND NOT r.rolreplication
        AND NOT r.rolbypassrls
        AND pg_get_userbyid(d.datdba) = r.rolname
        AND has_database_privilege(
            r.rolname, '${TEST_DATABASE}', 'CONNECT'
        )
        AND NOT has_database_privilege(
            r.rolname, '${DEV_DATABASE}', 'CONNECT'
        )
    FROM pg_roles r
    JOIN pg_database d
        ON d.datname = '${TEST_DATABASE}'
    WHERE r.rolname = '${TEST_ROLE}'
), FALSE);
")"

if [[ "${isolation_valid}" != "t" ]]; then
    echo "ERROR: PostgreSQL test database isolation validation failed." >&2
    exit 1
fi

echo "PostgreSQL test database isolation: OK"
echo "Moviely test database provisioning completed successfully."
