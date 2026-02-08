#!/bin/bash
set -e

# Wait for MySQL to be ready
echo "⏳ Waiting for MySQL to start..."
until mysqladmin ping -h "$DB_HOST" --silent; do
    sleep 1
done

echo "✅ MySQL is up, running custom SQL..."
mysql -u root -p "$DB_NAME" < /sql_init/sql_init.sql
