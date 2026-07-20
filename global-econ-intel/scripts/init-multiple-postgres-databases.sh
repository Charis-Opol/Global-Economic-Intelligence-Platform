#!/bin/bash
# Creates one Postgres database per name listed in POSTGRES_MULTIPLE_DATABASES.
# Airflow, MLflow, and Superset each get an isolated database on the same
# Postgres instance so we don't need three separate metadata containers.
set -e
set -u

function create_database() {
	local database=$1
	echo "Creating database '$database'"
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
	    CREATE DATABASE "$database";
	    GRANT ALL PRIVILEGES ON DATABASE "$database" TO "$POSTGRES_USER";
EOSQL
}

if [ -n "${POSTGRES_MULTIPLE_DATABASES:-}" ]; then
	echo "Multiple database creation requested: $POSTGRES_MULTIPLE_DATABASES"
	IFS=',' read -ra DB_ARRAY <<< "$POSTGRES_MULTIPLE_DATABASES"
	for db in "${DB_ARRAY[@]}"; do
		create_database "$db"
	done
	echo "Multiple databases created"
fi
