#!/bin/bash
set -e

if ! odbcinst -q -d -n "ODBC Driver 18 for SQL Server" >/dev/null 2>&1; then
  . /etc/os-release
  curl -sSL https://packages.microsoft.com/keys/microsoft.asc \
    | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg
  curl -sSL "https://packages.microsoft.com/config/${ID}/${VERSION_ID}/prod.list" \
    | sed 's#deb \[#deb [signed-by=/usr/share/keyrings/microsoft-prod.gpg #' \
    > /etc/apt/sources.list.d/mssql-release.list
  apt-get update
  ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc
fi

exec gunicorn -k uvicorn.workers.UvicornWorker -w 1 -b 0.0.0.0:8000 \
  --timeout 300 --forwarded-allow-ips "*" app.main:app