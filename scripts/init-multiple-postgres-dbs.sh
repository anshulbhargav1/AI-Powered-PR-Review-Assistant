#!/bin/bash
# Runs once on first postgres container startup (mounted into
# /docker-entrypoint-initdb.d/). Creates one database per name listed in
# POSTGRES_MULTIPLE_DATABASES, since the official postgres image only creates
# a single database (POSTGRES_DB) out of the box, and this stack needs three:
# pr_review (app data) plus temporal + temporal_visibility (Temporal server).
set -e
set -u

function create_database() {
    local database=$1
    echo "Creating database '$database'"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
        CREATE DATABASE $database;
        GRANT ALL PRIVILEGES ON DATABASE $database TO $POSTGRES_USER;
EOSQL
}

if [ -n "${POSTGRES_MULTIPLE_DATABASES:-}" ]; then
    echo "Multiple database creation requested: $POSTGRES_MULTIPLE_DATABASES"
    for db in $(echo "$POSTGRES_MULTIPLE_DATABASES" | tr ',' ' '); do
        create_database "$db"
    done
    echo "Multiple databases created"
fi
