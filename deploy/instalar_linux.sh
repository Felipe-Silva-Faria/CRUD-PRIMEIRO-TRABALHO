#!/usr/bin/env bash
set -euo pipefail

DESTINO=/opt/crud-ativos

echo "[1/6] Pacotes do sistema"
apt-get update -qq
apt-get install -y -qq python3 python3-venv curl

echo "[2/6] Usuario de servico sem shell (menor privilegio)"
id crud &>/dev/null || useradd --system --no-create-home --shell /usr/sbin/nologin crud

echo "[3/6] Codigo e ambiente virtual"
mkdir -p "$DESTINO"
cp -r config.py api algoritmos dominio estruturas persistencia servicos utilitarios requirements-docker.txt "$DESTINO"/
python3 -m venv "$DESTINO/.venv"
"$DESTINO/.venv/bin/pip" install -q -r "$DESTINO/requirements-docker.txt"
chown -R root:root "$DESTINO"

echo "[4/6] Pastas de dados e logs (as unicas com escrita)"
install -d -o crud -g crud -m 750 /var/lib/crud-ativos /var/log/crud-ativos
install -d -m 700 /etc/crud-ativos
[ -f /etc/crud-ativos/api.env ] || {
  echo "CRUD_API_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')" > /etc/crud-ativos/api.env
  chmod 600 /etc/crud-ativos/api.env
}

echo "[5/6] Servico systemd"
cp deploy/crud-api.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now crud-api

echo "[6/6] Verificacao"
sleep 2
systemctl --no-pager status crud-api | head -5
curl -fsS http://127.0.0.1:8000/health && echo
